import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("config/.env")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API Key not found in config/.env")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

try:
    response = model.generate_content("Hello, respond with 'OK' if you can hear me.")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
