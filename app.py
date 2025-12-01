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
from brain import create_mind_flow_brain, load_user_profile

# --- 安全關鍵字（Guardrails） ---
SAFETY_KEYWORDS = [
    # English
    "suicide",
    "kill myself",
    "want to die",
    "want to end it all",
    "end my life",
    "self-harm",
    "self harm",
    # Chinese
    "自殺",
    "想死",
    "不想活了",
    "活不下去",
    "想結束一切",
    "傷害自己",
]

SAFETY_MESSAGE = (
    "⚠️ 我注意到你提到可能與自我傷害或生命安全有關的內容。\n\n"
    "我是一個 AI，沒有醫療或心理專業資格，也無法在緊急狀況中提供即時協助。\n\n"
    "👉 如果你有**立即的危險**，請立刻聯絡你所在地的緊急電話（例如 911），\n"
    "或撥打當地的自殺防治／心理諮詢專線，並尋求家人、朋友或信任的人陪伴你。\n\n"
    "你值得被好好對待，也值得被真正看見和幫助。"
)

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
    
    # 調試：顯示 user_profile 狀態
    if st.checkbox("🔍 顯示調試信息", False):
        user_profile = load_user_profile()
        st.write("**User Profile 狀態:**")
        st.json(user_profile)
        if st.button("🗑️ 清除對話記錄（測試用）"):
            if "messages" in st.session_state:
                del st.session_state.messages
            st.rerun()
    
    st.subheader("🧭 你的導航系統")
    
    # 從 JSON 文件加載用戶配置文件
    user_profile = load_user_profile()
    
    if user_profile.get("vision"):
        st.markdown(f"**🔭 願景:** {user_profile['vision']}")
        st.markdown(f"**⚙️ 系統:** {user_profile['system']}")
        st.info("💡 Starter 會根據你的當前狀態動態生成微行動建議")
    else:
        st.warning("尚未建立系統。請與 Strategist 互動以設定你的 12 週願景！")
    
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
    
    # 根據 user_profile 的狀態決定使用哪個 Agent
    from brain import get_strategist_greeting, get_returning_user_greeting
    # 從 JSON 文件加載用戶配置文件
    user_profile = load_user_profile()
    
    # 檢查是否已完成 onboarding（system 已設置）
    if user_profile.get("system"):
        # 老用戶：直接使用 Starter（啟動）或 Healer（關心）
        # 預設使用 Starter（啟動模式），如果需要 Healer 可以改為 "healer"
        with st.spinner("🚀 Starter 正在準備問候（老用戶模式）..."):
            greeting_response = get_returning_user_greeting(
                api_key=api_key, 
                model="gemini-2.0-flash",
                plan_state=user_profile,
                agent_type="starter"  # 或 "healer" 用於關心模式
            )
    else:
        # 新用戶或未完成 onboarding：使用 Strategist
        with st.spinner("🧠 Strategist 正在準備問候..."):
            greeting_response = get_strategist_greeting(
                api_key=api_key, 
                model="gemini-2.0-flash",
                plan_state=user_profile
            )
    
    st.session_state.messages.append(greeting_response)

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

    # 1.5 安全檢查：自我傷害／生命危險關鍵字（硬守門）
    lowered = prompt.lower()
    if any(keyword in lowered for keyword in SAFETY_KEYWORDS):
        # 直接用固定模板回覆，不進入大腦／不調用任何工具
        safety_ai_message = AIMessage(content=SAFETY_MESSAGE)
        st.session_state.messages.append(safety_ai_message)
        st.chat_message("assistant").write(SAFETY_MESSAGE)
        st.warning("⚠️ 安全守門機制已觸發，此輪對話不會進入 Mind Flow 大腦。")
    else:
        # 2. 執行 Agent
        with st.spinner("Mind Flow 團隊正在協作中..."):
            result = st.session_state.mind_flow_app.invoke({"messages": st.session_state.messages})
            response = result["messages"][-1]
        
        # 3. 顯示 AI Response
        st.session_state.messages.append(response)
        st.chat_message("assistant").write(response.content)
        
        # 4. 如果有 Tool Call，顯示成功提示
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # 檢查是哪種工具被調用
            for tool_call in response.tool_calls:
                tool_name = getattr(tool_call, 'name', None) or (tool_call.get('name') if isinstance(tool_call, dict) else None)
                if tool_name == "save_journal_entry":
                    st.toast("✨ 日記已寫入資料庫！查看側邊欄數據。", icon="✅")
                elif tool_name == "set_full_plan":
                    st.toast("✨ 計劃已建立！查看側邊欄導航系統。", icon="🎯")
                    st.rerun()  # 重新運行以更新側邊欄顯示
