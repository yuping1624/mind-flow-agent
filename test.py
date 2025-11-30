"""
Mind Flow Test - 終端機測試腳本
用於快速測試大腦邏輯，無需啟動 Streamlit 介面
"""
import os
import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from brain import create_mind_flow_brain


def get_greeting():
    """根據時間返回問候語"""
    current_hour = datetime.datetime.now().hour
    if 5 <= current_hour < 12:
        return "早安。新的一天開始了。你想先設定今天的『核心目標』(Strategist)，還是覺得有點沒動力(Healer)？"
    elif 12 <= current_hour < 18:
        return "午後好。今天進度如何？如果卡住了，我們隨時可以微調目標。"
    else:
        return "晚上好。今天辛苦了。要不要花 2 分鐘結算一下今天的狀態 (Architect)？"


def main():
    """主測試循環"""
    # 載入環境變數
    load_dotenv()
    
    # 獲取 API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = input("請輸入 Google API Key: ").strip()
        if not api_key:
            print("❌ 需要 API Key 才能運行")
            return
    
    print("🧠 Mind Flow - 終端測試模式")
    print("=" * 50)
    print("輸入 'quit' 或 'exit' 退出\n")
    
    # 創建大腦（不使用 journal_db，因為終端測試不需要持久化）
    app = create_mind_flow_brain(api_key=api_key, model="gemini-2.0-flash")
    
    # 初始化對話
    messages = []
    greeting = get_greeting()
    print(f"🤖 {greeting}\n")
    messages.append(AIMessage(content=greeting))
    
    # 對話循環
    while True:
        # 獲取用戶輸入
        user_input = input("👤 你: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("\n👋 再見！")
            break
        
        # 添加用戶訊息
        messages.append(HumanMessage(content=user_input))
        
        # 執行大腦
        print("\n🤔 Mind Flow 團隊正在協作中...\n")
        try:
            result = app.invoke({"messages": messages})
            response = result["messages"][-1]
            
            # 顯示回應
            print(f"🤖 {response.content}\n")
            
            # 如果有工具調用，顯示提示
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print("✨ [工具已執行]\n")
            
            # 更新訊息歷史
            messages.append(response)
            
        except Exception as e:
            print(f"❌ 錯誤: {e}\n")
            # 移除最後的用戶訊息，以便重試
            messages.pop()


if __name__ == "__main__":
    main()

