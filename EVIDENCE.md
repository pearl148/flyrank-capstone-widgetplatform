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
_(todo)_

## Public submission API
_(todo)_

## Abuse protection
_(todo)_

## Enrichment & safe side effects
_(todo)_

## Documentation
_(todo)_