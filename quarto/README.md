# Template VAC Project

This is a template VAC project created with `sunholo init quarto`


## Test calls


```shell
export FLASK_URL=http://127.0.0.1:8080

curl -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Report if quarto is working"
}'

curl -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Please render a hello world Quarto html page"
}'

curl -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: multipart/form-data" \
  -F "user_input=Please render this markdown file" \
  -F "markdown_file=@tools/demo.qmd"
```