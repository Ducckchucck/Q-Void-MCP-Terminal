# modules/real_gemini.py
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Gemini API key not found. Please set GEMINI_API_KEY in your .env file.")
    model = None
else:
    genai.configure(api_key=api_key)  # type: ignore
    model = genai.GenerativeModel('gemini-1.5-pro')  # type: ignore
    print("✅ Gemini configured successfully")


async def generate_response(prompt):
    if not model:
        return "My AI service is currently unavailable."
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ Generation error: {e}")
        return "I couldn't process that request."