
#!/bin/sh
export $(egrep -v '^#' .env | xargs)
mkdir -p build
cp -r skill build
cp requirements.txt build
yc serverless function version create \
    --function-id $MY_FUNCTION_ID \
    --source-path build \
    --runtime python37-preview \
    --entrypoint skill.main.handler \
    --memory 128M \
    --execution-timeout 5s \
    --environment "DEBUG=True"
