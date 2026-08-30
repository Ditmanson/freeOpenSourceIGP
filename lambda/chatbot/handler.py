import json
from datetime import datetime, timezone, timedelta

import boto3
from botocore.exceptions import ClientError

# --- Model / region -----------------------------------------------------

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-2"

# --- Tunable limits -------------------------------------------------------
# Edit these to constrict/expand the cost/abuse envelope. No other code
# changes are needed to change these values.

MAX_REQUESTS_PER_IP_PER_HOUR = 10
MAX_INPUT_CHARS = 1000
MAX_OUTPUT_TOKENS = 300
MONTHLY_SPEND_CEILING_USD = 10.00

# Claude Haiku 4.5 pricing (per Anthropic's published rates, as of this
# writing) - used only to estimate spend for the circuit-breaker, not for
# billing itself.
INPUT_COST_PER_TOKEN_USD = 1.00 / 1_000_000
OUTPUT_COST_PER_TOKEN_USD = 5.00 / 1_000_000

# Worst-case cost of a single request, used to *reserve* budget atomically
# before calling Bedrock - see _reserve_monthly_spend. ~4 chars/token is a
# standard rough estimate for English text.
_ESTIMATED_MAX_INPUT_TOKENS = MAX_INPUT_CHARS // 4
_MAX_REQUEST_COST_MICRODOLLARS = round(
    (
        _ESTIMATED_MAX_INPUT_TOKENS * INPUT_COST_PER_TOKEN_USD
        + MAX_OUTPUT_TOKENS * OUTPUT_COST_PER_TOKEN_USD
    )
    * 1_000_000
)

RATE_LIMIT_TABLE = "chatbot-limits"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.client("dynamodb", region_name=REGION)


def handler(event, context):
    ip = _get_source_ip(event)

    if not _check_and_increment_ip_limit(ip):
        return _response(
            429,
            {
                "error": "You've asked a lot of questions recently. "
                "Please wait a bit and try again."
            },
        )

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    question = (body.get("question") or "").strip()
    if not question:
        return _response(400, {"error": "Missing 'question'"})
    if len(question) > MAX_INPUT_CHARS:
        return _response(
            400, {"error": f"Question is too long (max {MAX_INPUT_CHARS} characters)."}
        )

    # Reserve worst-case spend atomically *before* calling Bedrock, so
    # concurrent requests can't all pass a stale pre-check and collectively
    # blow past the ceiling (see ticket 02's code review for why the
    # earlier read-then-write version was a real race, not just
    # theoretical).
    if not _reserve_monthly_spend():
        return _response(
            429,
            {
                "error": "The chatbot has hit its monthly usage limit. "
                "Please try again next month."
            },
        )

    try:
        result = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": MAX_OUTPUT_TOKENS,
                    "messages": [{"role": "user", "content": question}],
                }
            ),
        )
        payload = json.loads(result["body"].read())
        answer = payload["content"][0]["text"]

        usage = payload.get("usage", {})
        actual_cost_microdollars = round(
            usage.get("input_tokens", 0) * INPUT_COST_PER_TOKEN_USD * 1_000_000
            + usage.get("output_tokens", 0) * OUTPUT_COST_PER_TOKEN_USD * 1_000_000
        )
        _true_up_monthly_spend(actual_cost_microdollars)

        return _response(200, {"answer": answer})
    except Exception as e:
        print("Bedrock invoke failed:", str(e))
        # The reserved budget was never actually spent - refund it in full.
        _true_up_monthly_spend(0)
        return _response(502, {"error": "Something went wrong answering your question."})


# --- Rate limiting / spend circuit-breaker --------------------------------


def _get_source_ip(event):
    return event.get("requestContext", {}).get("http", {}).get("sourceIp", "unknown")


def _current_month_key():
    return f"spend#{datetime.now(timezone.utc).strftime('%Y-%m')}"


def _spend_ttl():
    # Keep spend records around for 2 months, then let them expire - each
    # month gets its own key anyway, this is just table tidiness.
    return int((datetime.now(timezone.utc) + timedelta(days=62)).timestamp())


def _check_and_increment_ip_limit(ip):
    now = datetime.now(timezone.utc)
    hour_bucket = now.strftime("%Y-%m-%dT%H")
    pk = f"ip#{ip}#{hour_bucket}"
    ttl = int((now + timedelta(hours=2)).timestamp())

    result = dynamodb.update_item(
        TableName=RATE_LIMIT_TABLE,
        Key={"pk": {"S": pk}},
        UpdateExpression="ADD #c :incr SET #t = if_not_exists(#t, :ttl)",
        ExpressionAttributeNames={"#c": "count", "#t": "ttl"},
        ExpressionAttributeValues={":incr": {"N": "1"}, ":ttl": {"N": str(ttl)}},
        ReturnValues="UPDATED_NEW",
    )
    count = int(result["Attributes"]["count"]["N"])
    return count <= MAX_REQUESTS_PER_IP_PER_HOUR


def _reserve_monthly_spend():
    """Atomically add this request's worst-case cost to the monthly total,
    but only if doing so would keep the total under the ceiling - single
    conditional UpdateItem, so concurrent requests are correctly serialized
    by DynamoDB rather than racing on a separate read-then-write.
    """
    pk = _current_month_key()
    ceiling_microdollars = round(MONTHLY_SPEND_CEILING_USD * 1_000_000)
    threshold = ceiling_microdollars - _MAX_REQUEST_COST_MICRODOLLARS

    try:
        dynamodb.update_item(
            TableName=RATE_LIMIT_TABLE,
            Key={"pk": {"S": pk}},
            UpdateExpression="ADD microdollars :incr SET #t = if_not_exists(#t, :ttl)",
            ConditionExpression="attribute_not_exists(microdollars) OR microdollars < :threshold",
            ExpressionAttributeNames={"#t": "ttl"},
            ExpressionAttributeValues={
                ":incr": {"N": str(_MAX_REQUEST_COST_MICRODOLLARS)},
                ":threshold": {"N": str(threshold)},
                ":ttl": {"N": str(_spend_ttl())},
            },
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def _true_up_monthly_spend(actual_cost_microdollars):
    """Correct the ledger from the worst-case reservation down to (or up
    to, though that shouldn't happen given max_tokens is capped) the real
    cost of this specific request.
    """
    diff = actual_cost_microdollars - _MAX_REQUEST_COST_MICRODOLLARS
    if diff == 0:
        return
    dynamodb.update_item(
        TableName=RATE_LIMIT_TABLE,
        Key={"pk": {"S": _current_month_key()}},
        UpdateExpression="ADD microdollars :diff",
        ExpressionAttributeValues={":diff": {"N": str(diff)}},
    )


def _response(status, body_dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body_dict),
    }
