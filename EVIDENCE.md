//Evidence of tenant isolation

curl -X 'GET' \
  'http://localhost:8000/widgets' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmN0ZWNoQGdtYWlsLmNvbSIsInVzZXJfaWQiOjEsInRlbmFudF9pZCI6MSwiZXhwIjoxNzkyNTY5MTU4fQ.RBUJM5Ep4tsEBHt2ijJi7-fvvN1VP6t_W8VHETrEZoU'
Request URL
http://localhost:8000/widgets
Server response
Code	Details
200	
Response body

[]
Response headers
 content-length: 2 
 content-type: application/json 
 date: Wed,21 Oct 2026 06:53:02 GMT 
 server: uvicorn 
Responses