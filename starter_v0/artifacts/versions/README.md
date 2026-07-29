# Reproducible optimization artifacts

Mỗi version là một thí nghiệm riêng:

| Version | System prompt | Tool declarations | Hypothesis |
|---|---|---|---|
| v1 | `v1/system_prompt.md` | `v1/tools.yaml` | Làm rõ missing-info và consent boundary. |
| v2 | `v2/system_prompt.md` | `v1/tools.yaml` | Giữ nguyên arguments và trạng thái multi-turn. |
| v3 | `../system_prompt.md` | `../tools.yaml` | Làm rõ routing trong tool declarations. |

Không chạy các version liên tiếp mà không đọc run trước. Các snapshot chỉ giúp
khóa đúng artifact/hash; metric và tên run chỉ được ghi sau khi có run thật.

