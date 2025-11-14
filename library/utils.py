import logging
from typing import List
from asgiref.sync import async_to_sync
from google import genai
from config.settings import GEMINI_API_KEY


client = genai.Client(api_key=GEMINI_API_KEY)


async def _ai_search_books_async(query: str, language: str = "uz") -> List[str]:
    try:
        system_instruction = (
            "Siz kutubxona qidiruv yordamchisisiz. Foydalanuvchi tabiiy tilda kitob qidiryapti. "
            "Ularning so'rovini tahlil qilib, qidiruv uchun kalit so'zlarni ajratib bering. "
            "Faqat kalit so'zlarni vergul bilan ajratib qaytaring. Boshqa hech narsa yozmang. "
            "Misol: \"men romantik kitob izlayapman\" -> \"romantika, sevgi, munosabat\". "
            f"Javob tili: {language}."
        )

        chat = client.aio.chats.create(model="gemini-2.5-flash")

        prompt = (
            f"{system_instruction}\n\n"
            f"Foydalanuvchi so'rovi: {query}\n\n"
            "Faqat kalit so'zlarni vergul bilan ajratib yozing."
        )

        response = await chat.send_message(prompt)

        text = response.text or ""

        keywords = [k.strip() for k in text.split(",") if k.strip()]

        return keywords or [query]

    except Exception as e:
        logging.error(f"AI search error (Gemini): {e}")
        return [query]


def ai_search_books(query: str, language: str = "uz") -> List[str]:
    return async_to_sync(_ai_search_books_async)(query=query, language=language)
