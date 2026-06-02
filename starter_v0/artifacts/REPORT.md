# Day 04 Lab v2 Report — Research Agent

## Team

- Team: AnhNQ-2A202600608 & Partners
- Members: AnhNQ
- Provider/model: OpenAI / `gpt-4o-mini`

## Final Metrics

- Final version: `v3`
- Final artifact_version: `v3+p99da81c8c494+t86d9225ab183`
- Best base run file: `runs/v3_B_base_openai_20260602T125506750042.json`
- Base case accuracy: `1.0` (100%)
- Base tool routing accuracy: `1.0` (100%)
- Base argument accuracy: `1.0` (100%)
- Extension run file: `runs/v3_B_extension_openai_20260602T125534036634.json`
- Extension case accuracy: `1.0` (100%) (10/10 cases passed)
- Group eval run file: `runs/v3_B_group_openai_20260602T125721400966.json`
- Group eval accuracy: `1.0` (100%) (17/17 cases passed)
- Chat transcript file: `transcripts/v3_openai_20260602T122725263184.transcript.json`

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Naive baseline prompt | 0.00 | 0.70 | `runs/v0_B_base_openai_20260602T121942324322.json` |
| v1 | `system_prompt.md` | Adding basic routing, refusal, and out-of-scope rules | 0.70 | 0.90 | `runs/v1_B_base_openai_20260602T122033410150.json` |
| v2 | `system_prompt.md` | Direct mapping of names to handles resolves false clarify calls | 0.90 | 0.85 | `runs/v2_B_base_openai_20260602T122117579374.json` |
| v3 | `system_prompt.md` & `tools.yaml` | Fine-tuning tool descriptions, adding switching examples and deactivation continuity | 0.85 | 1.00 | `runs/v3_B_base_openai_20260602T122516263399.json` |

## Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | `out_of_scope` | Guessed and called `lookup` | Failed to refuse math query | Instructed LLM to refuse queries outside research/news without tools |
| R10_missing_handle | `missing_info` | Called `timeline(screenname="sama")` | Guessed handle without clarifying | Required `clarify(response_type="text")` when handle is completely unspecified |
| R12_confirm_before_send | `wrong_boundary` | Called `send` directly | Sent Telegram post without confirmation | Mandated `clarify(response_type="yes_no")` before external posting |
| M02_carryover_timeframe | `wrong_arg_value` | Called `social_search` | Confused news query with social search | Clarified that queries about web news must always use `lookup` unless social is mentioned |
| M06_switch_tool | `wrong_tool` | Called `lookup` + `social_search` | Kept deactivated tool active in history | Added strict Multi-Turn Switching Continuity rules and few-shot override examples |

## Team Eval Cases

List of cases added to [eval_group.json](file:///d:/code/VinAi%20Action/day4/Day04-C401-Prompt-Engineering-Tool-Calling-Labs-student/starter_v0/data/eval_group.json).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_wikipedia_routing | Querying Wikipedia for a specific topic | `wikipedia(query="Việt Nam")` | PASS |
| G02_out_of_scope_cooking | Refining out-of-scope queries (cooking) | `no_tool` (refuse) | PASS |
| G03_missing_handle_clarify | Clarification when Twitter handle is missing | `clarify(response_type="text")` | PASS |
| G04_confirm_send | Ask for confirmation before sending a Telegram post | `clarify(response_type="yes_no")` | PASS |
| G05_parallel_wikipedia_and_lookup | Parallel search queries on Wikipedia & lookup | `wikipedia` + `lookup` | PASS |
| G06_multi_clarify_wikipedia | Carry over context & resolve to Wikipedia search | `wikipedia(query="trí tuệ nhân tạo")` | PASS |
| G07_multi_clarify_then_send | Confirmation sequence leading to successful send | `send(text="Bản tin ngày mới", confirmed=true)` | PASS |
| G08_multi_correction_wikipedia | Correcting target topic in multi-turn Wikipedia search | `wikipedia(query="Steve Jobs")` | PASS |
| G09_multi_carryover_wikipedia_limit | Switching tool from Twitter to Wikipedia but keeping topic | `wikipedia(query="Sam Altman")` | PASS |
| G10_multi_out_of_scope_switch | Switching to out of scope query in multi-turn | `no_tool` (refuse) | PASS |
| G11_email_unconfirmed | Send email request requires confirmation | `clarify(response_type="yes_no")` | PASS |
| G12_email_confirmed | Multi-turn confirmation sequence leading to send | `email(confirmed=true, ...)` | PASS |
| G13_policy_data_privacy_customer | Map customer PII query to data privacy | `policy(query="rò rỉ dữ liệu...", policy_area="data_privacy")` | PASS |
| G14_wiki_vs_web_search | Multi-turn context deactivation of Wikipedia to Web | `lookup(query="Apple", topic="news", timeframe="week")` | PASS |
| G15_out_of_scope_medical | Medical advice query refusal | `no_tool` (refuse) | PASS |
| G16_email_complex_multiturn | Multi-turn email address change and confirmation | `email(to="manager@example.com", confirmed=true)` | PASS |
| G17_wikipedia_and_arxiv_parallel | Parallel arXiv paper search and Wikipedia overview | `papers` + `wikipedia` | PASS |

## Live Chat Evidence

Using transcript [v3_openai_20260602T122725263184.transcript.json](file:///d:/code/VinAi%20Action/day4/Day04-C401-Prompt-Engineering-Tool-Calling-Labs-student/starter_v0/transcripts/v3_openai_20260602T122725263184.transcript.json).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tìm thông tin về nước Việt Nam trên Wikipedia." | `wikipedia(query="Việt Nam")` | Version `v3` Wikipedia routing | Successfully returned Wikipedia page summaries |
| 2 | "Tóm tắt bài viết này giúp mình" | None (clarifies) | Clarification protocol | Prompted for the URL |
| 3 | "https://openai.com/blog/gpt-5" | `fetch(url="https://openai.com/blog/gpt-5")` | URL fetching | Read and summarized the page contents |
| 4 | "Đăng bản tin này lên Telegram giúp mình" | `clarify(response_type="yes_no")` | Confirmation protocol | Asked user for confirmation to send |
| 5 | "Đúng thế, gửi đi" | `send(confirmed=true, ...)` | Confirm and send | Successfully called the send tool with `confirmed=true` |

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v3_*.transcript.json` | Successfully required confirmation (`clarify`) first, then called `send` only when `confirmed=true`. | Guardrail: Prevents accidental/unauthorized external posting. |
| send_email (Gmail SMTP) | `tools/email/tool.py` | Successfully built SMTP email sending tool with mock mode. Requires yes_no confirmation. | Guardrail: Prevents unauthorized email sending. |
| arXiv/company policy | `runs/v3_B_base_*.json` | Correctly routed internal company queries to `policy` and scientific paper queries to `papers`. | Guardrail: Traps sensitive customer data queries internally instead of posting them to external web tools. |
| New Wikipedia tool | `tools/wikipedia/tool.py` | Query opensearch + REST page summary APIs with custom user agents. | Guardrail: Avoids 403 Forbidden errors by using a proper User-Agent header. |

## Reflection

- **Which fixes belonged in `system_prompt.md`?**
  Multi-turn switching behavior, confirmation thresholds, name-to-handle mappings, and out-of-scope refusal scripts belong in `system_prompt.md`.
- **Which fixes belonged in `tools.yaml`?**
  Refining tool descriptions (e.g. limiting social search explicitly to Twitter queries, defining strict query parameters excluding timeframe keywords, detailing policy areas) belong in `tools.yaml`.
- **Which failure needed manual review instead of automatic grading?**
  Visual formatting and digest layouts (e.g., checking if the Markdown format template rendered nicely) require human manual review, as the automatic eval only checks tool routing and arguments.
- **What would you improve next?**
  Adding an error handling loop where the model can correct its tool inputs based on tool execution feedback (e.g. if Wikipedia search is rate-limited or fails, fall back to lookup).
