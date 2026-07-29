# translate

Dịch văn bản sang ngôn ngữ khác. Dùng khi user yêu cầu dịch một đoạn text sang ngôn ngữ cụ thể.

## Khi nào dùng

- User nói "dịch đoạn này sang ...", "translate this to ..."
- User đã cung cấp text cần dịch rõ ràng

## Khi nào KHÔNG dùng

- User chưa cung cấp text → gọi `clarify(response_type="text")` trước
- User chỉ hỏi thông tin chung (dùng `lookup` thay thế)

## Arguments

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `text` | Có | Đoạn văn bản cần dịch (tối đa 500 ký tự) |
| `source_lang` | Không | Ngôn ngữ gốc, mặc định `"auto"` (tự nhận diện) |
| `target_lang` | Không | Ngôn ngữ đích, mặc định `"vi"` (tiếng Việt). Dùng `"en"` cho tiếng Anh, `"ja"` cho tiếng Nhật |

## Quicktest

```python
from tools import TOOL_FUNCTIONS
result = TOOL_FUNCTIONS["translate"](text="Hello world", target_lang="vi")
print(result)
```

## Implementation

Sử dụng MyMemory Translation API (free, không cần API key).

- Endpoint: `https://api.mymemory.translated.net/get`
- Rate limit: 5000 ký tự/ngày cho anonymous requests
