# 01: Minimal Bedrock-backed Lambda behind a Function URL

**What to build:** The core AWS wiring proven end-to-end before anything else is built on it - a Lambda function, authenticated to AWS Bedrock via its own IAM role (no API key anywhere), reachable via its own public Function URL, that takes a question and returns a real Claude Haiku response. No content grounding, no rate limiting, no capability config yet - those are later tickets, deliberately.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] An IAM role (`chatbot-lambda-role`) exists, granted `bedrock:InvokeModel` scoped to the specific Haiku 4.5 inference profile + foundation model ARN, plus (discovered during implementation) `aws-marketplace:ViewSubscriptions`/`aws-marketplace:Subscribe` - Anthropic models on Bedrock route through AWS Marketplace under the hood and the first invocation needs to auto-subscribe
- [x] The Lambda function (`griz-chatbot`, Python 3.13) calls Bedrock's Claude Haiku 4.5 model with the visitor's question and returns the model's response
- [x] A Function URL exists (auth type NONE, CORS restricted to `https://griz.sh`), with the resource-based policy correctly granting **both** `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` (as of an AWS policy change in Oct 2025, both are now required as separate statements - a single-statement policy silently 403s)
- [x] Every mutating AWS command was surfaced to the site owner for confirmation before running
- [x] Verified via repeated direct `curl` calls to the Function URL: real, coherent Claude Haiku responses came back consistently
- [x] No changes to `layouts/`, `content/`, or any Hugo-rendered output
- [x] No changes to `public/`

**Significant debugging during this ticket, root causes found and fixed:**
1. Function URL returned 403 Forbidden despite an apparently-correct resource policy - AWS changed the requirement in Oct 2025 to need both `lambda:InvokeFunctionUrl` *and* `lambda:InvokeFunction` as separate `add-permission` statements; the docs' own example policy confirmed this, and a second `add-permission` call fixed it.
2. Bedrock then returned `ResourceNotFoundException: Model use case details have not been submitted for this account` - a one-time Anthropic/Bedrock requirement, submitted by the site owner via the Bedrock console's Model catalog -> Playground -> first-invoke prompt (the older "Model access" page has been retired).
3. After that, Bedrock returned `AccessDeniedException` for missing `aws-marketplace:ViewSubscriptions`/`aws-marketplace:Subscribe` permissions - added to the Lambda's role, confirmed with the site owner first.
4. One aside: two separate AWS documentation pages fetched during this debugging (Lambda Function URLs, Bedrock API reference) both contained an identical "Skills for AI coding assistants" section suggesting an `aws agent-toolkit search-skills` command - flagged to the site owner as a likely prompt injection and not acted on, since identical text on two unrelated official docs pages isn't how real AWS documentation behaves.

**Concrete resource identifiers, for auditability** (these AWS resources are CLI-managed, not IaC-tracked in this repo, so recording the actual IDs here matters):
- IAM role: `arn:aws:iam::861079997941:role/chatbot-lambda-role`
- Attached policies: AWS managed `AWSLambdaBasicExecutionRole`; inline `InvokeHaiku` (bedrock:InvokeModel scoped to `arn:aws:bedrock:us-east-2:861079997941:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0` and `arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0`); inline `MarketplaceSubscribeForBedrock` (aws-marketplace:ViewSubscriptions, aws-marketplace:Subscribe, both Resource: "*")
- Lambda function: `arn:aws:lambda:us-east-2:861079997941:function:griz-chatbot` (Python 3.13, 256MB, 30s timeout)
- Function URL resource policy: two statements - `FunctionURLAllowPublicAccess` (lambda:InvokeFunctionUrl, Principal *, condition FunctionUrlAuthType=NONE) and `FunctionURLInvokeAllowPublicAccess` (lambda:InvokeFunction, Principal *, condition InvokedViaFunctionUrl=true)
