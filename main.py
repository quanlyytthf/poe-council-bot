import fastapi_poe as fp
from typing import AsyncIterable
import os

# Danh sách các Bot thật sự bạn muốn gọi (Handle chuẩn trên Poe)
# Bạn có thể thêm bớt tùy ý
EXPERT_BOTS = {
    "ChienLuoc_GPT4": "GPT-4o",
    "SangTao_Claude": "Claude-3.5-Sonnet",
    "PhanBien_Gemini": "Gemini-1.5-Pro"
}

class CouncilBot(fp.PoeBot):
    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
        user_input = request.query[-1].content
        
        # 1. Thông báo mở cuộc họp
        yield fp.PartialResponse(text=f"🤖 **Đang gửi yêu cầu đến hội đồng AI...**\nChủ đề: {user_input}\n\n---\n")

        # Biến lưu nội dung để tổng hợp sau cùng
        full_context = f"Vấn đề cần giải quyết: {user_input}\n\n"

        # 2. Gọi từng con BOT THẬT SỰ
        for role, bot_name in EXPERT_BOTS.items():
            yield fp.PartialResponse(text=f"⏳ Đang lấy ý kiến từ **{bot_name}**...\n")
            
            bot_response = ""
            try:
                # Lệnh này gọi API sang bot khác và chờ kết quả về
                async for msg in fp.stream_request(request, bot_name, request.query):
                    bot_response += msg.text
                
                # In kết quả của bot đó ra ngay cho bạn xem
                yield fp.PartialResponse(text=f"\n> **[{bot_name}]:**\n{bot_response}\n\n")
                
                # Lưu vào bộ nhớ để tí nữa tổng hợp
                full_context += f"Ý kiến của {bot_name}:\n{bot_response}\n---\n"
                
            except Exception as e:
                yield fp.PartialResponse(text=f"❌ Lỗi kết nối với {bot_name}: {e}\n")

        # 3. Tổng hợp kết quả (Dùng Claude để tóm tắt lại các ý kiến trên)
        yield fp.PartialResponse(text="💎 **TỔNG KẾT & ĐÁNH GIÁ CUỐI CÙNG**\n")
        
        final_prompt = fp.ProtocolMessage(
            role="user", 
            content=f"Hãy đóng vai người ra quyết định cuối cùng. Dựa trên các ý kiến sau đây, hãy đưa ra kết luận và bảng so sánh:\n{full_context}"
        )

        async for msg in fp.stream_request(request, "Claude-3.5-Sonnet", [final_prompt]):
            yield msg

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        # Khai báo các bot phụ thuộc để Poe cấp quyền
        deps = {name: 1 for name in EXPERT_BOTS.values()}
        return fp.SettingsResponse(server_bot_dependencies=deps)

# Cấu hình khởi chạy Server
if __name__ == "__main__":
    import uvicorn
    # Lấy port từ môi trường (bắt buộc cho Render)
    port = int(os.environ.get("PORT", 8080)) 
    uvicorn.run("main:app", host="0.0.0.0", port=port)
else:
    # Dòng này để Render chạy qua lệnh gunicorn/uvicorn
    app = fp.make_app(CouncilBot(), allow_without_key=True)