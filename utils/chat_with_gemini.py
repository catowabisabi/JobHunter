import os
import google.generativeai as genai
from dotenv import load_dotenv

def setup_gemini():
    """Setup Gemini API with your API key."""
    load_dotenv()  # Load API key from .env file
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("Please set your GOOGLE_API_KEY in the .env file")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    return model

def chat_with_gemini():
    """Start a chat session with Gemini."""
    try:
        model = setup_gemini()
        chat = model.start_chat(history=[])
        
        print("歡迎使用 Gemini AI 聊天程式！")
        print("輸入 'quit' 或 'exit' 來結束對話")
        
        while True:
            user_input = input("\n你: ")
            
            if user_input.lower() in ['quit', 'exit']:
                print("謝謝使用，再見！")
                break
            
            response = chat.send_message(user_input)
            print("\nGemini:", response.text)
            
    except Exception as e:
        print(f"發生錯誤: {str(e)}")

if __name__ == "__main__":
    chat_with_gemini() 