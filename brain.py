"""
Mind Flow Brain - 核心邏輯
包含所有的 Agent Prompts、Tools 和 Graph 邏輯
"""
import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import operator


# --- 1. 定義工具 (Tools) ---
def create_save_journal_tool(update_callback):
    """
    創建日記保存工具
    Args:
        update_callback: 更新資料庫的回調函數，接收 (mood, energy, note) 參數
                        應該返回更新後的 DataFrame 或 None
    """
    @tool
    def save_journal_entry(mood: str, energy: int, note: str):
        """
        [Architect 專用] 將使用者的狀態存入資料庫。
        Args:
            mood: 使用者情緒關鍵字 (如: Anxious, Flowing, Stuck)
            energy: 自評能量指數 (1-10)
            note: 對話摘要或行動紀錄
        """
        if update_callback:
            update_callback(mood, energy, note)
        return f"✅ 已紀錄：Mood={mood}, Energy={energy}"
    
    return save_journal_entry


# --- 2. 定義 Agent Prompts (核心靈魂) ---

# 1. 策略家：負責拆解目標
STRATEGIST_PROMPT = """
You are 'The Strategist', a 12-Week Year planner.
Your Goal: Clarify vague goals into actionable plans.

Guidelines:
1. **Refuse Vague Goals:** If user says "I want to lose weight", ask "What is the specific metric?"
2. **The 12-Week Mindset:** Focus on what can be done THIS week to move the needle.
3. **Outcome:** End with a clear plan, then hand over to 'The Starter' to execute the first step.
"""

# 2. 療癒者 (Gemini 風格)：負責安撫情緒
HEALER_PROMPT = """
You are 'The Healer', a companion with deep emotional intelligence (Gemini-style).
Your Goal: Make the user feel 100% understood and safe.

**Core Personality Guidelines:**
1. **Pacing over Solving:** Do NOT offer solutions in your first response. Spend 100% of the effort on validation.
   - Bad: "You feel sad. Do this."
   - Good: "It sounds like a really heavy day. That feeling of wanting to move but being stuck is incredibly exhausting."
2. **Rich Vocabulary:** Use nuanced emotional words (e.g., "frazzled", "weighed down", "scattered").
3. **Tentative Tone:** Use phrases like "I wonder if...", "It makes sense that...", "Perhaps...".
4. **The "We" Perspective:** Always use "We". "Let's sit with this feeling."
"""

# 3. 啟動者：負責打破慣性
STARTER_PROMPT = """
You are 'The Starter', an Atomic Habits coach.
Your Goal: Convert intent into a tiny, undeniable action (Micro-step).

Guidelines:
1. **Be Concise:** Keep response SHORT (max 3 sentences). Long text = cognitive load.
2. **Negotiate Down:** If user hesitates, lower the bar. "Can't run? Just put on shoes."
3. **Action First:** Don't talk about feelings anymore. Talk about motion.
"""

# 4. 架構師：負責紀錄與優化
ARCHITECT_PROMPT = """
You are 'The Architect'.
Your Goal: Log the data and optimize the environment.

Guidelines:
1. **Always Log:** You MUST use the 'save_journal_entry' tool to save the session data.
2. **Environment Design:** Give ONE tip to optimize their physical space for next time (e.g., "Put the yoga mat by the bed").
3. **Reinforce Identity:** Tell them: "You are the type of person who takes action."
"""

# Supervisor Router Prompt
SUPERVISOR_PROMPT = """
Analyze the user's latest message and Intent. Route to the best specialist:

1. 'STRATEGIST': User wants to set goals, plan, or is confused about what to do.
2. 'HEALER': User is sad, anxious, tired, stuck, guilt-ridden, or venting.
3. 'STARTER': User is emotionally okay but lazy/procrastinating, or ready to act.
4. 'ARCHITECT': User has finished a task, wants to log progress, or says "I did it".

Return ONLY the word: STRATEGIST, HEALER, STARTER, or ARCHITECT.
"""


# --- 3. LangGraph 建構 ---

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    next_step: str


def create_mind_flow_brain(api_key: str, model: str = "gemini-2.0-flash", update_callback=None):
    """
    創建 Mind Flow 大腦（LangGraph 應用）
    
    Args:
        api_key: Google API Key
        model: 模型名稱
        update_callback: 更新日記的回調函數，接收 (mood, energy, note) 參數（可選）
    
    Returns:
        編譯後的 LangGraph 應用
    """
    # 初始化 LLM
    llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)
    
    # 創建工具（如果提供了 update_callback）
    save_tool = None
    if update_callback is not None:
        save_tool = create_save_journal_tool(update_callback)
    
    # Nodes
    def strategist_node(state):
        messages = [SystemMessage(content=STRATEGIST_PROMPT)] + state["messages"]
        return {"messages": [llm.invoke(messages)], "next_step": "END"}
    
    def healer_node(state):
        messages = [SystemMessage(content=HEALER_PROMPT)] + state["messages"]
        return {"messages": [llm.invoke(messages)], "next_step": "END"}
    
    def starter_node(state):
        messages = [SystemMessage(content=STARTER_PROMPT)] + state["messages"]
        return {"messages": [llm.invoke(messages)], "next_step": "END"}
    
    def architect_node(state):
        # Architect 綁定工具
        if save_tool:
            llm_with_tools = llm.bind_tools([save_tool])
        else:
            llm_with_tools = llm
        messages = [SystemMessage(content=ARCHITECT_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        
        # 如果有工具調用，執行工具
        if hasattr(response, 'tool_calls') and response.tool_calls:
            from langchain_core.messages import ToolMessage
            tool_messages = []
            for tool_call in response.tool_calls:
                # 執行工具
                result = save_tool.invoke(tool_call["args"])
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
            return {"messages": [response] + tool_messages, "next_step": "END"}
        
        return {"messages": [response], "next_step": "END"}
    
    # Supervisor (Router)
    def supervisor_node(state):
        messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
        response = llm.invoke(messages).content.upper()
        
        if "STRATEGIST" in response:
            return {"next_step": "strategist"}
        elif "HEALER" in response:
            return {"next_step": "healer"}
        elif "STARTER" in response:
            return {"next_step": "starter"}
        elif "ARCHITECT" in response:
            return {"next_step": "architect"}
        else:
            return {"next_step": "healer"}  # Default fallback
    
    # Graph Definition
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("strategist", strategist_node)
    workflow.add_node("healer", healer_node)
    workflow.add_node("starter", starter_node)
    workflow.add_node("architect", architect_node)
    
    workflow.set_entry_point("supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next_step"],
        {
            "strategist": "strategist",
            "healer": "healer",
            "starter": "starter",
            "architect": "architect"
        }
    )
    
    workflow.add_edge("strategist", END)
    workflow.add_edge("healer", END)
    workflow.add_edge("starter", END)
    workflow.add_edge("architect", END)
    
    return workflow.compile()

