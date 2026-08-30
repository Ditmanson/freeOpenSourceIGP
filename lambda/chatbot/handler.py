import json

import boto3

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-2"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    question = (body.get("question") or "").strip()
    if not question:
        return _response(400, {"error": "Missing 'question'"})

    try:
        result = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": question}],
                }
            ),
        )
        payload = json.loads(result["body"].read())
        answer = payload["content"][0]["text"]
        return _response(200, {"answer": answer})
    except Exception as e:
        print("Bedrock invoke failed:", str(e))
        return _response(502, {"error": "Something went wrong answering your question."})


def _response(status, body_dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body_dict),
    }
