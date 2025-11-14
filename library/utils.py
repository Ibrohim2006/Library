# import os
# import uuid
# import logging
# from typing import List
# from asgiref.sync import async_to_sync
# from your_llm_client import LlmChat, UserMessage
#
#
# async def _ai_search_books_async(query: str, language: str = "uz") -> List[str]:
#     """
#     Use AI to understand natural language query and extract search terms (ASYNC core).
#     """
#     try:
#         emergent_key = os.environ.get("EMERGENT_LLM_KEY")
#         if not emergent_key:
#             raise Exception("EMERGENT_LLM_KEY not found")
#
#         chat = (
#             LlmChat(
#                 api_key=emergent_key,
#                 session_id=str(uuid.uuid4()),
#                 system_message=(
#                     "Siz kutubxona qidiruv yordamchisisiz. Foydalanuvchi tabiiy tilda kitob qidiryapti.\n"
#                     "Ularning so'rovini tahlil qilib, qidiruv uchun kalit so'zlarni ajratib bering.\n"
#                     "Faqat kalit so'zlarni vergul bilan ajratib qaytaring. Boshqa hech narsa yozmang.\n"
#                     'Misol: "men romantik kitob izlayapman" -> "romantika, sevgi, munosabat"\n'
#                     f"Til: {language}"
#                 ),
#             )
#             .with_model("openai", "gpt-4o")
#         )
#
#         user_message = UserMessage(text=query)
#         response = await chat.send_message(user_message)
#
#         # LLM javobidan kalit so'zlarni ajratish
#         keywords = [k.strip() for k in response.split(",") if k.strip()]
#         return keywords or [query]
#
#     except Exception as e:
#         logging.error(f"AI search error: {e}")
#         # Fallback: AI ishlamasa, oddiy matnni o'zini kalit so'z sifatida qaytaramiz
#         return [query]
#
#
# def ai_search_books(query: str, language: str = "uz") -> List[str]:
#     """
#     DRF (sync view) ichida chaqirish uchun SINK wrapper.
#     async -> sync ga asgiref orqali o'giradi.
#     """
#     return async_to_sync(_ai_search_books_async)(query, language)
