/# EVIDENCE

One proof per requirement. Each section: what it proves, the command, the output.

## Widget management

### Auth required: requests without a valid token are rejected
**Proves:** protected endpoints return 401 without valid auth.

```bash
curl -i -X POST http://localhost:8000/widgets \
  -H "Authorization: Bearer not-a-real-token" \
  -H "Content-Type: application/json" \
  -d '{"type":"signup_form","title":"x","fields":{},"button_text":"Go"}'
```

```
HTTP/1.1 401 Unauthorized
{"detail":"Invalid or expired token"}
```

### Multi-tenant isolation
**Proves:** tenant B cannot read, change or delete tenant A's widget.
```bash
curl -X 'GET' \
  'http://localhost:8000/widgets/2' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmN0ZWNoQGdtYWlsLmNvbSIsInVzZXJfaWQiOjEsInRlbmFudF9pZCI6MSwiZXhwIjoxNzkyNTg4NTk2fQ.oklomNhSK-83pMdOD-JgII3E_2466QUW59worCmeFzk'
```
```
HTTP/1.1 404 Not Found
{"detail":"Widget not found"}
```

```bash
curl -X 'PUT' \
  'http://localhost:8000/widgets/2' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmN0ZWNoQGdtYWlsLmNvbSIsInVzZXJfaWQiOjEsInRlbmFudF9pZCI6MSwiZXhwIjoxNzkyNTg4NTk2fQ.oklomNhSK-83pMdOD-JgII3E_2466QUW59worCmeFzk' \
  -H 'Content-Type: application/json' \
  -d '{
  "title": "Changed content of another tenant widget",
  "description": "string",
  "fields": {
    "additionalProp1": {}
  },
  "button_text": "string",
  "display_options": {
    "additionalProp1": {}
  }
}'

```

```
HTTP/1.1 404 Not Found
{"detail":"Widget not found"}
```
```bash
curl -X 'DELETE' \
  'http://localhost:8000/widgets/2' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmN0ZWNoQGdtYWlsLmNvbSIsInVzZXJfaWQiOjEsInRlbmFudF9pZCI6MSwiZXhwIjoxNzkyNTg4NTk2fQ.oklomNhSK-83pMdOD-JgII3E_2466QUW59worCmeFzk'
```
```
HTTP/1.1 404 Not Found
{"detail":"Widget not found"}
```


## Widget delivery

**Proves:** `widget.v1.js` is served with `Cache-Control: public, max-age=31536000, immutable`, so browsers can cache it forever safely. Unknown or malformed versions (`v9`, `evil`) return a clean 404 and cannot be used to read other files.
```bash
curl -i http://localhost:8000/widget.v1.js
```
```
HTTP/1.1 200 OK
date: Fri, 23 Oct 2026 09:29:29 GMT
server: uvicorn
cache-control: public, max-age=31536000, immutable
content-type: application/javascript
accept-ranges: bytes
content-length: 1952
last-modified: Fri, 23 Oct 2026 09:23:52 GMT
etag: "d7d6967802bff4345f173bf19973c9cc"

(function(){
    var script = document.currentScript;
    var src = new URL(script.src);
    var API = src.origin;
    var widgetId = src.searchParams.get("id");
    if(!widgetId){
        console.error("Widget: missing ?id= in script URL");
        return;
    }

    fetch(API + "/widgets/" + encodeURIComponent(widgetId) + "/config")
    .then(function(r){
        if(!r.ok) throw new Error("Config request failed: " + r.status);
        return r.json();
    })
    .then(function(config){
        render(config);
    })
    .catch(function(err){
        console.error("Widget failed to load:", err);
    });

    function render(config){
        const div = document.createElement("div");
        div.className = "widget";
        script.parentNode.insertBefore(div,script)
        const h3 = document.createElement("h3");
        h3.textContent = config.title;
        div.appendChild(h3);
        if(config.fields){
            Object.entries(config.fields).forEach(([name,def])=>{
                const fieldDiv = document.createElement('div');
                fieldDiv.className = "widget-field";
                const label = document.createElement('label');
                label.textContent = def.label;
                label.htmlFor = name;

                const input = document.createElement('input');
                input.type = def.type || 'text';
                input.name = name;
                const inputId = "w-" + widgetId + "-" + name;
                input.id = inputId;
                label.htmlFor = inputId;
                input.required = Boolean(def.required);

                fieldDiv.appendChild(label);
                fieldDiv.appendChild(input);
                div.appendChild(fieldDiv);

            });
        }

        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = config.button_text || 'Submit';
        div.appendChild(button);
    }
})();(base)
```
```bash
curl -i http://localhost:8000/widget.v9.js
```
```
HTTP/1.1 404 Not Found
date: Thu, 22 Oct 2026 12:13:49 GMT
server: uvicorn
content-length: 22
content-type: application/json
{"detail":"Not found"}

```
```bash
 curl -i http://localhost:8000/widget.evil.js

```
```
HTTP/1.1 404 Not Found
date: Thu, 22 Oct 2026 12:14:35 GMT
server: uvicorn
content-length: 22
content-type: application/json

{"detail":"Not found"}
```
**Proves:** `widget.v1.js`is properly rendered in a second-origin page without the CORS blocing it

```bash
curl -i http://localhost:8000/widgets/4N-QbyjARpw/config \
  -H "Origin: http://localhost:5500"
  ```
  ```
  HTTP/1.1 200 OK
date: Fri, 23 Oct 2026 10:19:13 GMT
server: uvicorn
content-length: 490
content-type: application/json
cache-control: public, max-age=60
access-control-allow-origin: *

{"public_id":"4N-QbyjARpw","type":"signup_form","title":"Create Your Account","description":"Join our platform by filling out your details below.","fields":{"fullName":{"label":"Full Name","type":"text","required":true},"email":{"label":"Email Address","type":"email","required":true},"password":{"label":"Password","type":"password","required":true},"age":{"label":"Age (Optional)","type":"number","required":false}},"button_text":"Sign Up","display_options":{"theme":"light"},"version":1}
```
**Proves:** The preflight is also handled
```bash
curl -i -X OPTIONS http://localhost:8000/widgets/4N-QbyjARpw/config \
  -H "Origin: http://localhost:5500" \
  -H "Access-Control-Request-Method: GET"
```
```
HTTP/1.1 200 OK
date: Fri, 23 Oct 2026 10:24:00 GMT
server: uvicorn
access-control-allow-origin: *
access-control-allow-methods: GET, POST, OPTIONS
access-control-max-age: 600
access-control-allow-headers: Accept, Accept-Language, Content-Language, Content-Type
content-length: 2
content-type: text/plain; charset=utf-8
```



## Public submission API

### Valid submissions are stored

**Proves:** a valid cross-origin POST returns 201 and `{"id", "status"}` only (no tenant or IP leaked). Omitting the optional `age` field still succeeds.

```bash
curl -i -X POST http://localhost:8000/submissions   -H "Content-Type: application/json"   -H "Origin: http://localhost:5500"   -d '{
    "widget_id": "4N-QbyjARpw",
    "data": {
      "fullName": "John Doe",
      "email": "john@example.com",
      "password": "securepassword123",
      "age": "25"
    }
  }'

```
```HTTP/1.1 201 Created
date: Fri, 23 Oct 2026 12:53:23 GMT
server: uvicorn
content-length: 26
content-type: application/json
access-control-allow-origin: *

{"id":1,"status":"stored"}
```
```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{
    "widget_id": "4N-QbyjARpw",
    "data": {
      "fullName": "John Doe",
      "email": "john@example.com",
      "password": "securepassword123"
    }
  }'
```
```
HTTP/1.1 201 Created
date: Fri, 23 Oct 2026 12:59:54 GMT
server: uvicorn
content-length: 26
content-type: application/json
access-control-allow-origin: *

{"id":2,"status":"stored"}
```

### Invalid input returns a clean 4xx JSON error, never a 500

**Proves:** unknown fields, missing or whitespace-only required fields, a bad email, a non-string value, a malformed body and an unknown widget each get a 4xx with a JSON body.

```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{
    "widget_id": "4N-QbyjARpw",
    "data": {
      "fullName": "John Doe",
      "email": "john@example.com",
      "password": "securepassword123",
      "extraField": "unexpected value"
    }
  }'
```
```
HTTP/1.1 422 Unprocessable Content
date: Fri, 23 Oct 2026 12:54:49 GMT
server: uvicorn
content-length: 41
content-type: application/json
access-control-allow-origin: *

{"detail":"Unknown field(s): extraField"}
```

```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{
    "widget_id": "4N-QbyjARpw",
    "data": {
      "fullName": "John Doe",
      "email": "john@example.com"
    }
  }'
```
```
HTTP/1.1 422 Unprocessable Content
date: Fri, 23 Oct 2026 12:56:23 GMT
server: uvicorn
content-length: 45
content-type: application/json
access-control-allow-origin: *

{"detail":"Missing required field: password"}
```
```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{
    "widget_id": "4N-QbyjARpw",
    "data": {
      "fullName": "   ",
      "email": "john@example.com",
      "password": "securepassword123"
    }
  }'
```
```
HTTP/1.1 422 Unprocessable Content
date: Fri, 23 Oct 2026 12:57:07 GMT
server: uvicorn
content-length: 45
content-type: application/json
access-control-allow-origin: *

{"detail":"Missing required field: fullName"}
```
```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{
    "widget_id": "4N-QbyjARpw",
    "data": {
      "fullName": "John Doe",
      "email": "nope",
      "password": "securepassword123"
    }
  }'
```
```
HTTP/1.1 422 Unprocessable Content
date: Fri, 23 Oct 2026 12:58:08 GMT
server: uvicorn
content-length: 54
content-type: application/json
access-control-allow-origin: *

{"detail":"Field email must be a valid email address"}
```

```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{
    "widget_id": "4N-QbyjARpw",
    "data": {
      "fullName": "John Doe",
      "email": 123,
      "password": "securepassword123"
    }
  }'
```
```
HTTP/1.1 422 Unprocessable Content
date: Fri, 23 Oct 2026 13:00:39 GMT
server: uvicorn
content-length: 41
content-type: application/json
access-control-allow-origin: *

{"detail":"Field email must be a string"}
```
```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{
    "widget_id": "non-existent-id-999",
    "data": {
      "fullName": "John Doe",
      "email": "john@example.com",
      "password": "securepassword123"
    }
  }'
```
```
HTTP/1.1 404 Not Found
date: Fri, 23 Oct 2026 13:01:36 GMT
server: uvicorn
content-length: 29
content-type: application/json
access-control-allow-origin: *

{"detail":"Widget not found"}
```
```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{bad'
```
```
HTTP/1.1 422 Unprocessable Content
date: Fri, 23 Oct 2026 13:03:16 GMT
server: uvicorn
content-length: 158
content-type: application/json
access-control-allow-origin: *

{"detail":[{"type":"json_invalid","loc":["body",1],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting property name enclosed in double quotes"}}]}
```
### Oversized payloads are rejected

**Proves:** a 20 KB body returns 413 with a JSON error, and the response still carries `access-control-allow-origin`, so a browser can read the error.

```bash
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d "{
    \"widget_id\": \"4N-QbyjARpw\",
    \"data\": {
      \"fullName\": \"$(python3 -c 'print("A" * 20000)')\",
      \"email\": \"john@example.com\",
      \"password\": \"securepassword123\"
    }
  }"
```
```
HTTP/1.1 413 Content Too Large
date: Fri, 23 Oct 2026 13:04:30 GMT
server: uvicorn
content-length: 30
content-type: application/json
access-control-allow-origin: *

{"detail":"Payload too large"}
```


## Abuse protection
_(todo)_

## Enrichment & safe side effects
_(todo)_

## Documentation
_(todo)_