"""
Mind Flow App - Streamlit 界面
只負責顯示和用戶交互，核心邏輯在 brain.py
"""
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import pandas as pd
import datetime
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from brain import create_mind_flow_brain

# --- 1. 初始化與設定 ---
load_dotenv()
st.set_page_config(page_title="Mind Flow", page_icon="🧠", layout="wide")

# CSS 優化 (讓介面更乾淨)
st.markdown("""
<style>
    .stChatMessage { font-family: 'Helvetica', sans-serif; }
    .stButton button { border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 側邊欄：設定與數據儀表板 ---
with st.sidebar:
    st.header("⚙️ Mind Flow Engine")
    
    # API Key 管理 (優先級: 環境變數 > Secrets > 手動輸入)
    # 1. 優先從環境變數讀取 (通過 load_dotenv() 從 .env 文件加載)
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # 2. 如果環境變數沒有，嘗試從 Streamlit Secrets 讀取
    if not api_key:
        try:
            if "GOOGLE_API_KEY" in st.secrets:
                api_key = st.secrets["GOOGLE_API_KEY"]
        except StreamlitSecretNotFoundError:
            pass  # secrets.toml 不存在，繼續下一步
    
    # 3. 如果都沒有，使用手動輸入
    if not api_key:
        api_key = st.text_input("Google API Key", type="password", help="請輸入 Gemini API Key")

    st.divider()
    
    # 初始化資料庫 (Session State 模擬)
    if "journal_db" not in st.session_state:
        st.session_state.journal_db = pd.DataFrame(columns=["Timestamp", "Mood", "Energy", "Note"])

    st.subheader("📊 Flow Journal")
    if not st.session_state.journal_db.empty:
        # 顯示最近 5 筆
        st.dataframe(st.session_state.journal_db.tail(5), hide_index=True)
        # 簡單趨勢圖
        st.line_chart(st.session_state.journal_db["Energy"])
    else:
        st.info("尚無數據，完成一次行動後會自動記錄。")

if not api_key:
    st.warning("請先輸入 API Key 才能啟動 Mind Flow。")
    st.stop()

# --- 3. 初始化大腦 ---
# 創建更新日記的回調函數
def update_journal(mood: str, energy: int, note: str):
    """更新日記資料庫的回調函數"""
    new_entry = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Mood": mood,
        "Energy": energy,
        "Note": note
    }
    st.session_state.journal_db = pd.concat(
        [st.session_state.journal_db, pd.DataFrame([new_entry])], 
        ignore_index=True
    )

# 使用 session_state 來緩存大腦實例，避免每次重新創建
if "mind_flow_app" not in st.session_state:
    st.session_state.mind_flow_app = create_mind_flow_brain(
        api_key=api_key,
        model="gemini-2.0-flash",
        update_callback=update_journal
    )

# --- 4. 使用者介面 (UX) ---

st.title("🧠 Mind Flow")
st.caption("From Anxiety to Action: Your AI Companion for Executive Function.")

# 初始化對話
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # 主動問候 (Proactive Greeting)
    current_hour = datetime.datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "早安。新的一天開始了。你想先設定今天的『核心目標』(Strategist)，還是覺得有點沒動力(Healer)？"
    elif 12 <= current_hour < 18:
        greeting = "午後好。今天進度如何？如果卡住了，我們隨時可以微調目標。"
    else:
        greeting = "晚上好。今天辛苦了。要不要花 2 分鐘結算一下今天的狀態 (Architect)？"
    
    st.session_state.messages.append(AIMessage(content=greeting))

# 顯示歷史訊息
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    elif isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)

# 建議膠囊 (Suggestion Chips) - 替代側邊欄按鈕
suggestions = ["🎯 幫我拆解目標", "😫 我現在好焦慮", "🐢 我想動但動不了", "✅ 我完成了！幫我紀錄"]
cols = st.columns(4)
selected_prompt = None

for i, suggestion in enumerate(suggestions):
    if cols[i].button(suggestion):
        selected_prompt = suggestion

# 輸入處理
if prompt := (st.chat_input("告訴我你現在的狀態...") or selected_prompt):
    # 1. 顯示 User Message
    st.chat_message("user").write(prompt)
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    # 2. 執行 Agent
    with st.spinner("Mind Flow 團隊正在協作中..."):
        result = st.session_state.mind_flow_app.invoke({"messages": st.session_state.messages})
        response = result["messages"][-1]
        
    # 3. 顯示 AI Response
    st.session_state.messages.append(response)
    st.chat_message("assistant").write(response.content)
    
    # 4. 如果有 Tool Call (Architect)，顯示成功提示
    if hasattr(response, 'tool_calls') and response.tool_calls:
        st.toast("✨ 日記已寫入資料庫！查看側邊欄數據。", icon="✅")
