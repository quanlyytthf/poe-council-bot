import fastapi_poe as fp
from typing import AsyncIterable
import os

# --- DANH SÁCH CÁC BOT CHUYÊN GIA ---
# Đây là tên Bot CHUẨN (Handle) trên Poe
EXPERT_BOTS = {
    "ChienLuoc_GPT": "GPT-4o",          
    "SangTao_Claude": "Claude-3.5-Sonnet", 
    "PhanBien_Gemini": "Gemini-1.5-Pro"    
}

class CouncilBot(fp.PoeBot):
    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
        user_input = request.query[-1].content
        
        # 1. Báo hiệu bot bắt đầu chạy
        yield fp.PartialResponse(text=f"🤖 **Hội đồng đang làm việc...**\nChủ đề: {user_input}\n\n---\n")

        full_context = f"Vấn đề: {user_input}\n\n"

        # 2. Gọi từng chuyên gia
        for role, bot_name in EXPERT_BOTS.items():
            yield fp.PartialResponse(text=f"⏳ **{bot_name}** đang suy nghĩ...\n")
            
            bot_response = ""
            try:
                # Gọi Bot và stream kết quả
                async for msg in fp.stream_request(request, bot_name, request.query):
                    bot_response += msg.text
                
                yield fp.PartialResponse(text=f"> ✅ **{bot_name}**: Xong.\n")
                full_context += f"Ý kiến của {bot_name}:\n{bot_response}\n---\n"
                
            except Exception as e:
                # In lỗi chi tiết ra để dễ debug
                yield fp.PartialResponse(text=f"❌ Lỗi kết nối {bot_name}: {str(e)}\n")

        # 3. Tổng hợp kết quả (Dùng Claude để chốt hạ)
        yield fp.PartialResponse(text="\n💎 **TỔNG KẾT & ĐÁNH GIÁ CUỐI CÙNG**\n")
        
        final_prompt = fp.ProtocolMessage(
            role="user", 
            content=f"Tổng hợp các ý kiến sau thành một báo cáo chi tiết:\n{full_context}"
        )

        try:
            async for msg in fp.stream_request(request, "Claude-3.5-Sonnet", [final_prompt]):
                yield msg
        except Exception as e:
            yield fp.PartialResponse(text=f"Lỗi phần tổng hợp: {str(e)}")

    # --- PHẦN QUAN TRỌNG NHẤT: XIN QUYỀN GỌI BOT KHÁC ---
    # Nếu thiếu đoạn này, Bot sẽ báo lỗi "Error communicating"
    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        # Tạo danh sách các bot cần xin quyền
        deps = {name: 1 for name in EXPERT_BOTS.values()}
        return fp.SettingsResponse(server_bot_dependencies=deps)

if __name__ == "__main__":
    import uvicorn
    # Render bắt buộc dùng port từ biến môi trường
    port = int(os.environ.get("PORT", 8080)) 
    uvicorn.run("main:app", host="0.0.0.0", port=port)
