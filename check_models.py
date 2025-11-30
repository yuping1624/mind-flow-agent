import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# 如果讀不到 .env，請直接把 key 貼在下面引號中
api_key = os.getenv("GOOGLE_API_KEY") 
genai.configure(api_key=api_key)

print("正在查詢可用模型...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"發生錯誤: {e}")