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
###Cross-origin submissions
**Proves:** A visitor on a different origin submits via the widget; the browser preflight is answered and the row is stored for the right tenant

```bash
curl -i -X OPTIONS http://localhost:8000/submissions \ons \
  -H "Origin: http://localhost:5500" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"
```
```
HTTP/1.1 200 OK
date: Mon, 26 Oct 2026 11:11:19 GMT
server: uvicorn
access-control-allow-origin: *
access-control-allow-methods: GET, POST, OPTIONS
access-control-max-age: 600
access-control-allow-headers: Accept, Accept-Language, Content-Language, Content-Type
content-length: 2
content-type: text/plain; charset=utf-8
```
```bash
sqlite3 app.db "select id, widget_id, tenant_id, data from submission order by id desc limit 1;"
```
```
4|1|1|{"fullName": "abhi verma", "email": "abv@gmail.com", "password": "abv@!@", "age": "18"}
```


## Abuse protection
**Proves:** Per-IP rate limiting rejects a burst with 429 and a Retry-After header, other endpoints stay available, and normal traffic is accepted again after the window.

```bash
for i in $(seq 1 15); do   curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/submissions     -H "Content-Type: application/json"     -d '{"widget_id":"4N-QbyjARpw","data":{"fullName":"A B","email":"a@b.com","password":"secret123"}}'; done | sort | uniq -c
```
```
  10 201
  5 429
```
## this shows that it has header that says when it crosses the rate-limit when to retry after how many seconds
```bash
 curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5500" \
  -d '{"widget_id":"4N-QbyjARpw","data":{"fullName":"A B","email":"a@b.com","password":"secret123"}}'
HTTP/1.1 429 Too Many Requests
date: Thu, 29 Oct 2026 11:29:29 GMT
server: uvicorn
retry-after: 56
content-length: 55
content-type: application/json
access-control-allow-origin: *

{"detail":"Too many requests. Please try again later."}
```

## other endpoints stay available
```bash
curl -i http://localhost:curl -i http://localhost:8000/health
HTTP/1.1 200 OK
date: Thu, 29 Oct 2026 11:29:52 GMT
server: uvicorn
content-length: 15
content-type: application/json
```
```
{"status":"ok"}
```
```bash
curl -i http://localhost:8000/widgets/4N-QbyjARpw/configQbyjARpw/config
HTTP/1.1 200 OK
date: Thu, 29 Oct 2026 11:30:02 GMT
server: uvicorn
content-length: 490
content-type: application/json
cache-control: public, max-age=60
```
```
{"public_id":"4N-QbyjARpw","type":"signup_form","title":"Create Your Account","description":"Join our platform by filling out your details below.","fields":{"fullName":{"label":"Full Name","type":"text","required":true},"email":{"label":"Email Address","type":"email","required":true},"password":{"label":"Password","type":"password","required":true},"age":{"label":"Age (Optional)","type":"number","required":false}},"button_text":"Sign Up","display_options":{"theme":"light"},"version":1}
```
**Proves:**That the honeypot is working it gives a normal message like it gives to every valid submission but it is never stored in the database
```bash
sqlite3 app.db "select count(*) from submission;"
```
```
24
```

```bash
curl -i -X POST http://localhost:8000/submissions -H "Content-Type: application/json" \
  -d '{"widget_id":"4N-QbyjARpw","data":{"fullName":"A B","email":"a@b.com","password":"secret123"},"website":"http://spam.example"}'
```
```
HTTP/1.1 201 Created
date: Thu, 29 Oct 2026 11:26:28 GMT
server: uvicorn
content-length: 39
content-type: application/json

{"id":0,"status":"Successfully Stored"}
```

```bash
sqlite3 app.db "select count(*) from submission;"
```
```
24
```


## Enrichment & safe side effects
“Geo providers are mocked by tools/mock_geo.py on port 9001; POST /toggle/{a|b}/{up|down} switches each one.”

### Provider A answers first when healthy

**Proves:** with both mock providers up, a submission is enriched by provider A (stored country `MockLand-A`, city `Alpha City`) and provider B is never needed.

```bash
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{"widget_id":"4N-QbyjARpw","data":{"fullName":"A B","email":"a@b.com","password":"secret123"}}'
sqlite3 app.db "select id, country, city from submission order by id desc limit 1;"
```
```
{"id":36,"status":"stored"}36|MockLand-A|Alpha City
```


### Fallback chain: provider A down, provider B answers

**Proves:** with provider A returning 503, the submission still returns 201 and is enriched by provider B (stored country `MockLand-B`, city `Beta City`). The API log shows the provider A failure.

```bash
curl -X POST http://localhost:9001/toggle/a/down
curl -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{"widget_id":"4N-QbyjARpw","data":{"fullName":"A B","email":"a@b.com","password":"secret123"}}'
sqlite3 app.db "select id, country, city from submission order by id desc limit 1;"
```
```
{"a":true,"b":false}{"id":37,"status":"stored"}37|MockLand-B|Beta City
```

### Degrade, never fail: all providers down

**Proves:** with both providers returning 503, `POST /submissions` still returns 201 and the row is stored with NULL country and city. The log shows both providers were tried and failed.

```bash
curl -X POST http://localhost:9001/toggle/b/down
curl -i -X POST http://localhost:8000/submissions \
  -H "Content-Type: application/json" \
  -d '{"widget_id":"4N-QbyjARpw","data":{"fullName":"A B","email":"a@b.com","password":"secret123"}}'
sqlite3 app.db "select id, country, city from submission order by id desc limit 1;"
```
```
{"a":true,"b":true}HTTP/1.1 201 Created
date: Sat, 31 Oct 2026 07:25:34 GMT
server: uvicorn
content-length: 27
content-type: application/json

{"id":38,"status":"stored"}38||
127.0.0.1:46744 - "GET /a/json/8.8.8.8?fields=status,country,city HTTP/1.1" 503 Service Unavailable
INFO:     127.0.0.1:46758 - "GET /b/8.8.8.8/json/ HTTP/1.1" 503 Service Unavailable
```
### Provider unreachable (connection refused)

**Proves:** with the geo service not running at all, the submission still returns 201 and is stored without geo data, so a dead network connection is handled the same way as an error response.
```bash
curl -i -X POST http://localhost:8000/submissions   -H "Content-Type: application/json"   -d '{"widget_id":"4N-QbyjARpw","data":{"fullName":"A B","email":"a@b.com","password":"secret123"}}'
HTTP/1.1 201 Created
date: Sat, 31 Oct 2026 07:43:39 GMT
server: uvicorn
content-length: 27
content-type: application/json
```
```
{"id":39,"status":"stored"}
```

## Documentation
_(todo)_