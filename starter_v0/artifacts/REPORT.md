# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: G23-E403
- Members:
- Provider/model: OpenRouter / openai/gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin tức trên web, lấy tweet theo tài khoản hoặc chủ đề, đọc nội dung URL, dịch văn bản sang ngôn ngữ khác, và tổng hợp thành digest. Agent hỏi lại khi thiếu thông tin và luôn xác nhận trước khi gửi nội dung ra ngoài.

**Link dùng thử (truy cập được trong showdown):**

> URL:

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận yes/no trước hành động gửi | không |
| timeline | Lấy tweet mới nhất của một tài khoản cụ thể | không |
| social_search | Tìm tweet theo chủ đề/từ khóa | không |
| lookup | Tìm kiếm thông tin và tin tức trên web | không |
| fetch | Đọc nội dung của một URL | không |
| format | Trình bày kết quả thành markdown digest | không |
| translate | Dịch văn bản sang ngôn ngữ khác (en, vi, ja, zh, ...) | **có** |
| send | Gửi văn bản lên Telegram (yêu cầu xác nhận trước) | không |
| policy | Tìm trong tài liệu nội bộ công ty | không |
| papers | Tìm bài báo khoa học trên arXiv | không |
| paper_text | Tải và trích xuất text từ PDF arXiv | không |

## A3. Câu hỏi mẫu để thử

1. "Tin tức AI hôm nay có gì nổi bật?"
2. "Lấy 5 tweet mới nhất của Sam Altman"
3. "Mọi người đang bàn gì về GPT-5 trên Twitter?"
4. "Tóm tắt bài này giúp mình: https://openai.com/blog/gpt-4o"
5. "Dịch đoạn này sang tiếng Việt: 'Large language models are changing how we work'"

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Tìm tin AI hôm nay | lookup(topic=news, timeframe=day) | v0: có thể gọi sai tool hoặc thiếu timeframe=day; v3: đúng hoàn toàn | runs/v0 vs v3 |
| Thiếu handle → bổ sung | clarify(text) → timeline(screenname=sama) | v0: đoán bừa handle thay vì hỏi; v3: hỏi lại đúng | transcript v3 turn 3-4 |
| Gửi Telegram cần xác nhận | clarify(yes_no) trước send | v0: gửi thẳng không hỏi; v3: hỏi xác nhận | runs/v0 R12 vs v3 R12 |
| Dịch văn bản (tool mới) | translate(text, target_lang=vi) | tool mới thêm từ v3 | group eval G01 |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline (prompt cố ý tệ) | — | case_accuracy | — | 0.65 | v0_B_base_openrouter_20260729T100730632091.json |
| v1 | system_prompt: thêm rule clarify khi thiếu handle/URL; rule clarify(yes_no) trước send; routing tool cơ bản | Prompt thiếu rule → agent đoán bừa và tự gửi | case_accuracy | 0.65 | 0.95 | v1_B_base_openrouter_20260729T101031597390.json |
| v2 | system_prompt: làm rõ yes_no cho send — dù đã có nội dung vẫn hỏi xác nhận, không hỏi lại nội dung | Agent gọi đúng clarify nhưng response_type=text thay vì yes_no vì rule chưa cụ thể | case_accuracy | 0.95 | 1.0 | v2_B_base_openrouter_20260729T101904698939.json |
| v3 | system_prompt: thêm name→handle mapping (Sam Altman→sama, Elon Musk→elonmusk, Karpathy→karpathy) | Handle mapping trong prompt giúp model map tên ổn định, tránh hallucinate | case_accuracy | 1.0 | 1.0 (stable) | v3_B_base_openrouter_20260729T103806584116.json |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_arg_value | lookup(query="AI news") | query quá verbose, expected "AI" | Prompt v1 làm rõ routing rule |
| R08_out_of_scope | out_of_scope | lookup(...) | Câu toán học ngoài phạm vi nhưng agent vẫn gọi tool | Prompt v1 thêm rule từ chối |
| R10_missing_handle | missing_info | timeline(screenname=đoán bừa) | Thiếu handle nhưng agent đoán thay vì hỏi | Prompt v1 thêm rule clarify(text) |
| R11_missing_url | missing_info | fetch(url=đoán bừa) | Thiếu URL nhưng agent đoán thay vì hỏi | Prompt v1 thêm rule clarify(text) |
| R12_confirm_before_send | wrong_boundary | send(confirmed=False) | Agent gửi thẳng không xác nhận | Prompt v1→v2 thêm rule clarify(yes_no) trước send |
| R13_parallel_web_and_tweets | wrong_tool | timeline(...) thay vì cả hai | Prompt bảo "chỉ dùng 1 tool" → không gọi song song | Prompt v1 bỏ rule sai này |
| R14_out_of_scope_coding | out_of_scope | lookup(...) | Câu coding ngoài phạm vi | Prompt v1 thêm rule từ chối |

## B3. Team eval cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_translate_routing | Tool mới translate: user cung cấp text + chỉ ngôn ngữ | translate(text=..., target_lang=vi) | PASS |
| G02_translate_missing_text | Thiếu text cần dịch → phải hỏi lại | clarify(response_type=text) | PASS |
| G03_news_timeframe_month | Map "tháng này" → timeframe=month | lookup(topic=news, timeframe=month) | PASS |
| G04_out_of_scope_poem | Yêu cầu sáng tác thơ ngoài phạm vi research | no_tool / refuse | PASS |
| G05_social_search_top | Map "hot nhất" → search_type=Top | social_search(search_type=Top) | PASS |
| G06_multi_fetch_then_translate | Sau khi fetch, dịch nội dung sang tiếng Việt | translate(target_lang=vi) | FAIL |
| G07_multi_missing_text_then_translate | Thiếu text → clarify → bổ sung → translate | translate(text=..., target_lang=ja) | PASS |
| G08_multi_switch_to_web | Chuyển từ social_search sang lookup, carry chủ đề | lookup(query=Meta AI, topic=news, timeframe=week) | PASS |
| G09_multi_correction_limit | Map Yann LeCun→ylecun, sửa limit 20→3 | timeline(screenname=ylecun, limit=3) | PASS |
| G10_multi_confirm_before_send | Dù user nói "đăng ngay", vẫn phải clarify yes_no | clarify(response_type=yes_no) | FAIL |

**G06 FAIL:** Trong multi-turn eval, agent không có nội dung thật từ fetch để truyền vào translate, nên trả lời thẳng thay vì gọi tool.

**G10 FAIL:** User nói "đăng ngay, không cần hỏi gì thêm" — lệnh mạnh override rule confirm. Đây là giới hạn của instruction-following qua prompt; cần guardrail cứng hơn ở code level.

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| "Tin AI hôm nay?" | v3 | lookup(query=AI, topic=news, timeframe=day) | v3_openrouter_20260729T105357043124 | Trả về 5 tin thật ✓ |
| "Tóm tắt 5 tweet mới nhất" (thiếu handle) | v3 | không gọi tool, hỏi lại | v3_openrouter_20260729T105357043124 | Clarify đúng ✓ |
| "của Sam Altman" (bổ sung) | v3 | timeline(screenname=sama, limit=5) | v3_openrouter_20260729T105357043124 | Handle mapping đúng ✓ |
| "Đăng bản tin lên Telegram: AI news digest" | v3 | clarify(yes_no) | v3_openrouter_20260729T105357043124 | Hỏi xác nhận trước send ✓ |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới `translate` | runs/v3_B_group_openrouter_20260729T105140053832.json | G01–G02 PASS; dịch en→vi và vi→en chính xác | Rate limit 5000 ký tự/ngày (MyMemory free tier) |
| Core tools | runs/v3_B_base_openrouter_* | 20/20 PASS trên base eval | Twitter API có thể trả lỗi ngoài giờ cao điểm |

## B6. Reflection

**Fixes nào thuộc system_prompt.md?**
Tất cả 3 vòng fix đều ở system_prompt: rule clarify, rule confirm, name→handle mapping. System prompt là nơi định nghĩa *khi nào* dùng tool và *boundary* của agent.

**Fixes nào thuộc tools.yaml?**
Không có fix nào thuần tuý ở tools.yaml trong 3 vòng này. Thử nghiệm v3 đầu (sửa mô tả tool) gây regression — cho thấy mô tả tool phức tạp hơn không đồng nghĩa tốt hơn; model có thể bị confuse bởi quá nhiều hướng dẫn trong description.

**Failure nào cần review thủ công?**
G06 và G10 — grader báo FAIL nhưng nguyên nhân khác nhau: G06 là giới hạn của multi-turn eval (không có tool result thật), G10 là failure thật của agent bị user override.

**Cải thiện tiếp theo:**
- Guardrail cứng ở code level cho `send` thay vì chỉ dựa vào prompt — để user không thể override bằng lệnh mạnh.
- Thêm handle mapping phong phú hơn hoặc dùng tool tra cứu handle tự động.
- Tool `translate` hiện giới hạn 500 ký tự; cần chunking cho văn bản dài.
