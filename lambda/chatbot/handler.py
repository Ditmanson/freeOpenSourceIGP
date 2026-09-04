import html
import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta

import boto3
from botocore.config import Config
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

# A user question can trigger at most this many Bedrock calls. The final
# call always has tools disabled, forcing a real text answer instead of
# yet another tool request - guarantees a bounded, predictable call count
# per question while still letting the model search more than once if its
# first query was too narrow.
MAX_TOOL_ITERATIONS = 3

# Claude Haiku 4.5 pricing (per Anthropic's published rates, as of this
# writing) - used only to estimate spend for the circuit-breaker, not for
# billing itself.
INPUT_COST_PER_TOKEN_USD = 1.00 / 1_000_000
OUTPUT_COST_PER_TOKEN_USD = 5.00 / 1_000_000

# Worst-case cost of a single user request, used to *reserve* budget
# atomically before calling Bedrock - see _reserve_monthly_spend. ~4
# chars/token is a standard rough estimate for English text. This can't be
# a fixed constant: every Bedrock call also resends the full site content
# index as system-prompt context (see _build_system_prompt), and that
# index grows as the site grows - see _max_request_cost_microdollars,
# which computes this from the real cached index size instead.
_ESTIMATED_MAX_INPUT_TOKENS = MAX_INPUT_CHARS // 4

# Conservative fallback for the system-prompt size, used only if this is
# somehow called before the content index has been fetched in this
# execution environment - see _max_request_cost_microdollars.
_FALLBACK_SYSTEM_PROMPT_TOKENS = 3000


def _max_request_cost_microdollars():
    """Worst case: every one of MAX_TOOL_ITERATIONS calls resends the full
    system prompt (site content index + instructions) plus the user's
    question. Deliberately conservative - it ignores that later calls in
    the loop also carry accumulated tool-result content, so it slightly
    overestimates rather than under."""
    if _content_index_cache is None:
        system_prompt_tokens = _FALLBACK_SYSTEM_PROMPT_TOKENS
    else:
        system_prompt_tokens = len(_build_system_prompt()) // 4
    per_call_input_tokens = system_prompt_tokens + _ESTIMATED_MAX_INPUT_TOKENS
    return round(
        (
            per_call_input_tokens * INPUT_COST_PER_TOKEN_USD
            + MAX_OUTPUT_TOKENS * OUTPUT_COST_PER_TOKEN_USD
        )
        * 1_000_000
        * MAX_TOOL_ITERATIONS
    )


RATE_LIMIT_TABLE = "chatbot-limits"

# --- Site content / capabilities -------------------------------------------

CONTENT_INDEX_URL = "https://griz.sh/index.json"
CAPABILITIES_FILE = os.path.join(os.path.dirname(__file__), "capabilities.json")
MAX_TOOL_RESULT_ITEMS = 5

SYSTEM_PROMPT_INSTRUCTIONS = (
    "You are a helpful assistant embedded on a personal dog-training blog. "
    "Answer visitor questions using the site's own published content - use "
    "the search_site_content and list_videos tools (when available) to find "
    "specific posts rather than guessing. Keep answers short and point "
    "people at the relevant post URL(s). Do not answer questions unrelated "
    "to this site's content from general knowledge; say you don't know and "
    "suggest they browse the site instead."
)

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.client("dynamodb", region_name=REGION)
# Short, non-retrying timeout - this client is only ever called from the
# rejection path (see _record_limit_metric), which is supposed to fail
# fast. A slow or throttled CloudWatch call should never be able to stall
# a 429 response for botocore's default ~60s.
cloudwatch = boto3.client(
    "cloudwatch",
    region_name=REGION,
    config=Config(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1}),
)

# Namespace for the custom metrics this Lambda publishes when it rejects a
# request - alarmed on via the same SNS topic ("grizsh") already used for
# the site's AppSync alarms, not a new notification channel.
METRIC_NAMESPACE = "GrizChatbot"

with open(CAPABILITIES_FILE) as f:
    _CAPABILITIES = json.load(f)["tools"]

# Cached across warm Lambda invocations - refetched whenever a new
# execution environment starts (e.g. after each real deploy), so the index
# stays reasonably current without needing to redeploy the Lambda just for
# a content change.
_content_index_cache = None


def handler(event, context):
    ip = _get_source_ip(event)

    if not _check_and_increment_ip_limit(ip):
        _record_limit_metric("RateLimitRejection")
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

    # Make sure the content index is cached before reserving spend, so the
    # reservation below reflects its real current size rather than the
    # conservative fallback (see _max_request_cost_microdollars). This
    # fetch was always required to answer the question anyway - just
    # moved earlier so the reservation can be accurate.
    try:
        _get_content_index()
    except Exception as e:
        print("Content index fetch failed:", str(e))
        return _response(502, {"error": "Something went wrong answering your question."})

    # Reserve worst-case spend atomically *before* calling Bedrock, so
    # concurrent requests can't all pass a stale pre-check and collectively
    # blow past the ceiling (see ticket 02's code review for why the
    # earlier read-then-write version was a real race, not just
    # theoretical).
    reserved_microdollars = _reserve_monthly_spend()
    if reserved_microdollars is None:
        _record_limit_metric("SpendCeilingRejection")
        return _response(
            429,
            {
                "error": "The chatbot has hit its monthly usage limit. "
                "Please try again next month."
            },
        )

    try:
        answer, total_input_tokens, total_output_tokens = _answer_question(question)

        actual_cost_microdollars = round(
            total_input_tokens * INPUT_COST_PER_TOKEN_USD * 1_000_000
            + total_output_tokens * OUTPUT_COST_PER_TOKEN_USD * 1_000_000
        )
        _true_up_monthly_spend(actual_cost_microdollars, reserved_microdollars)

        return _response(200, {"answer": _markdown_to_safe_html(answer)})
    except Exception as e:
        print("Bedrock invoke failed:", str(e))
        # The reserved budget was never actually spent - refund it in full.
        _true_up_monthly_spend(0, reserved_microdollars)
        return _response(502, {"error": "Something went wrong answering your question."})


# --- Question answering / tool use -----------------------------------------

# Claude's answers naturally use Markdown (bold, bullet lists, [text](url)
# links) - the widget wants real HTML with live links, not literal
# asterisks/brackets. The answer text is model output shaped by a visitor's
# own question, so it's never trusted as raw HTML: everything is escaped
# first, then only this fixed, small set of safe tags is added back by
# these two patterns. No raw HTML from the model can ever pass through.
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
# URLs exclude "*" so a bold marker can never match a span that starts
# inside an href attribute value - keeps the two substitutions from being
# able to interact across tag boundaries at all, not just harmlessly.
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)*]+)\)")


def _markdown_to_safe_html(text):
    rendered = html.escape(text, quote=True)
    rendered = _LINK_RE.sub(
        lambda m: '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>'.format(
            m.group(2), m.group(1)
        ),
        rendered,
    )
    rendered = _BOLD_RE.sub(r"<strong>\1</strong>", rendered)

    html_parts = []
    paragraph_lines = []
    list_items = []

    def flush_paragraph():
        if paragraph_lines:
            html_parts.append("<p>{}</p>".format("<br>".join(paragraph_lines)))
            paragraph_lines.clear()

    def flush_list():
        if list_items:
            html_parts.append(
                "<ul>{}</ul>".format("".join("<li>{}</li>".format(i) for i in list_items))
            )
            list_items.clear()

    for line in (l.strip() for l in rendered.strip().split("\n")):
        if not line:
            flush_paragraph()
            flush_list()
        elif line.startswith("- "):
            flush_paragraph()
            list_items.append(line[2:].strip())
        else:
            flush_list()
            paragraph_lines.append(line)

    flush_paragraph()
    flush_list()
    return "".join(html_parts)


def _answer_question(question):
    """Runs the tool-use conversation loop and returns (answer_text,
    total_input_tokens, total_output_tokens) across every Bedrock call made
    for this one question."""
    tools = _get_enabled_tools()
    messages = [{"role": "user", "content": question}]
    total_input_tokens = 0
    total_output_tokens = 0

    payload = None
    for i in range(MAX_TOOL_ITERATIONS):
        # The last allowed call never offers tools, so the model cannot
        # respond with another tool_use request - it's forced to synthesize
        # a real text answer from whatever tool results it already has.
        is_last_call = i == MAX_TOOL_ITERATIONS - 1
        payload = _invoke_bedrock(messages, None if is_last_call else tools)
        usage = payload.get("usage", {})
        total_input_tokens += usage.get("input_tokens", 0)
        total_output_tokens += usage.get("output_tokens", 0)

        if payload.get("stop_reason") != "tool_use":
            break

        messages.append({"role": "assistant", "content": payload["content"]})
        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": block["id"],
                "content": json.dumps(_execute_tool(block["name"], block.get("input", {}))),
            }
            for block in payload["content"]
            if block["type"] == "tool_use"
        ]
        messages.append({"role": "user", "content": tool_results})

    answer = next(
        (b["text"] for b in payload.get("content", []) if b.get("type") == "text"), ""
    )
    if not answer:
        answer = (
            "I couldn't find a clear answer to that in the site's content - "
            "try rephrasing your question or browsing the site directly."
        )
    return answer, total_input_tokens, total_output_tokens


def _invoke_bedrock(messages, tools):
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_OUTPUT_TOKENS,
        "system": [
            {
                "type": "text",
                "text": _build_system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": messages,
    }
    if tools:
        request_body["tools"] = tools

    result = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(request_body),
    )
    return json.loads(result["body"].read())


def _build_system_prompt():
    index = _get_content_index()
    compact_index = [
        {"title": p.get("title") or "", "url": p.get("url") or "", "tags": p.get("tags") or []}
        for p in index
    ]
    return (
        SYSTEM_PROMPT_INSTRUCTIONS
        + "\n\nSite content index (titles, URLs, tags - use search_site_content for "
        "full excerpts of any of these):\n"
        + json.dumps(compact_index)
    )


def _enabled_capabilities():
    return {t["name"]: t for t in _CAPABILITIES if t.get("enabled")}


def _get_enabled_tools():
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in _enabled_capabilities().values()
    ]


def _execute_tool(name, tool_input):
    if name not in _enabled_capabilities():
        # Defensive - the model was never told about this tool, so it
        # shouldn't be able to call it, but don't silently no-op if it
        # somehow does.
        return {"error": f"Tool '{name}' is not currently enabled."}

    if name == "search_site_content":
        return _search_site_content(tool_input.get("query", ""))
    if name == "list_videos":
        return _list_videos(tool_input.get("topic"))
    return {"error": f"Tool '{name}' has no implementation."}


def _search_site_content(query):
    query_lower = query.lower().strip()
    if not query_lower:
        return []
    matches = [p for p in _get_content_index() if query_lower in _page_haystack(p)]
    return [_page_result(p) for p in matches[:MAX_TOOL_RESULT_ITEMS]]


def _list_videos(topic=None):
    videos = [p for p in _get_content_index() if p.get("hasVideo")]
    if topic:
        topic_lower = topic.lower().strip()
        videos = [p for p in videos if topic_lower in _page_haystack(p)]
    return [_page_result(p) for p in videos[:MAX_TOOL_RESULT_ITEMS]]


def _page_haystack(page):
    # Content index pages come from Hugo's own build - trusted structurally,
    # but .get() rather than direct indexing means one page missing an
    # unexpected field degrades that page's matching instead of 502ing
    # every question.
    return " ".join(
        [page.get("title") or "", " ".join(page.get("tags") or []), page.get("summary") or ""]
    ).lower()


def _page_result(page):
    return {
        "title": page.get("title") or "",
        "url": page.get("url") or "",
        "tags": page.get("tags") or [],
        "excerpt": page.get("summary") or "",
    }


def _get_content_index():
    global _content_index_cache
    if _content_index_cache is None:
        with urllib.request.urlopen(CONTENT_INDEX_URL, timeout=5) as resp:
            _content_index_cache = json.loads(resp.read())
    return _content_index_cache


# --- Rate limiting / spend circuit-breaker --------------------------------


def _record_limit_metric(metric_name):
    """Synchronous, but failures are swallowed - a metric-publishing error
    should never break or delay-with-a-crash the actual rejection response
    the visitor gets."""
    try:
        cloudwatch.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=[{"MetricName": metric_name, "Value": 1, "Unit": "Count"}],
        )
    except Exception as e:
        print("Failed to publish limit metric:", str(e))


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
    by DynamoDB rather than racing on a separate read-then-write. Returns
    the reserved amount (needed later to true it up), or None if the
    reservation was rejected.
    """
    pk = _current_month_key()
    reserve_microdollars = _max_request_cost_microdollars()
    ceiling_microdollars = round(MONTHLY_SPEND_CEILING_USD * 1_000_000)
    threshold = ceiling_microdollars - reserve_microdollars

    try:
        dynamodb.update_item(
            TableName=RATE_LIMIT_TABLE,
            Key={"pk": {"S": pk}},
            UpdateExpression="ADD microdollars :incr SET #t = if_not_exists(#t, :ttl)",
            ConditionExpression="attribute_not_exists(microdollars) OR microdollars < :threshold",
            ExpressionAttributeNames={"#t": "ttl"},
            ExpressionAttributeValues={
                ":incr": {"N": str(reserve_microdollars)},
                ":threshold": {"N": str(threshold)},
                ":ttl": {"N": str(_spend_ttl())},
            },
        )
        return reserve_microdollars
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise


def _true_up_monthly_spend(actual_cost_microdollars, reserved_microdollars):
    """Correct the ledger from the worst-case reservation down to (or up
    to, though that shouldn't happen given max_tokens is capped) the real
    cost of this specific request.
    """
    diff = actual_cost_microdollars - reserved_microdollars
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
