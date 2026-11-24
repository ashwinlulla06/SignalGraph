from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

gemini_model = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    max_retries=3
)