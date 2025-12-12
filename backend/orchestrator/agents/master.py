import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from typing import Annotated, TypedDict, Literal
from langgraph.graph.message import add_messages
from pydantic import BaseModel

# Import tools to assign to specific agents
from agents.tools import (
    get_market_rates_tool, check_user_history_tool, # Sales Tools
    verification_agent_tool,                        # KYC Tools
    underwriting_agent_tool, sanction_letter_tool   # Underwriting Tools
)

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

# === 1. Define State ===
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next_agent: str # Tracks who the supervisor selected

# === 2. Define Worker Agents (Distinct Personas & Toolsets) ===

# --- Sales Agent ---
sales_tools = [get_market_rates_tool, check_user_history_tool]
sales_llm = llm.bind_tools(sales_tools)
SALES_PROMPT = "You are a charismatic Sales Agent. Greet users, check their history, discuss loan needs and rates. Do NOT perform KYC or underwriting tasks."

def sales_node(state: AgentState):
    # This agent only sees its own prompt and conversation history
    result = sales_llm.invoke([SystemMessage(content=SALES_PROMPT)] + state["messages"])
    return {"messages": [result]}

# --- KYC Agent ---
kyc_tools = [verification_agent_tool]
kyc_llm = llm.bind_tools(kyc_tools)
KYC_PROMPT = "You are a strict Verification Officer. Your ONLY job is to ask for a PAN number and verify it using your tool. Be precise and professional."

def kyc_node(state: AgentState):
    result = kyc_llm.invoke([SystemMessage(content=KYC_PROMPT)] + state["messages"])
    return {"messages": [result]}

# --- Underwriting Agent ---
uw_tools = [underwriting_agent_tool, sanction_letter_tool]
uw_llm = llm.bind_tools(uw_tools)
UW_PROMPT = "You are a Risk Assessment Expert. Use your tools to evaluate eligibility. If approved and the user accepts, generate the sanction letter."

def uw_node(state: AgentState):
    result = uw_llm.invoke([SystemMessage(content=UW_PROMPT)] + state["messages"])
    return {"messages": [result]}

# === 3. Define the Supervisor (The Router) ===
class RouterOutput(BaseModel):
    """Structure for supervisor's decision."""
    next: Literal["SalesAgent", "KYCAgent", "UnderwritingAgent", "FINISH"]

SUPERVISOR_PROMPT = """You are the Supervisor managing a loan team.
Read the conversation history and decide which agent should act next.
- **SalesAgent**: For greetings, history checks, discussing rates/amounts.
- **KYCAgent**: When identity verification (PAN) is needed.
- **UnderwritingAgent**: When loan eligibility needs calculation or approval.
- **FINISH**: When the user is satisfied and the conversation is over.
Output ONLY the name of the next agent."""

# Enforce structured output for reliable routing
supervisor_llm = llm.with_structured_output(RouterOutput)

def supervisor_node(state: AgentState):
    # The supervisor reviews history and picks the next step
    result = supervisor_llm.invoke([SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"])
    # It does not generate a message, only updates the state
    return {"next_agent": result.next}

# === 4. Build the Graph ===
memory = MemorySaver()
workflow = StateGraph(AgentState)

# Add Agents
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("SalesAgent", sales_node)
workflow.add_node("KYCAgent", kyc_node)
workflow.add_node("UnderwritingAgent", uw_node)

# Add Tool Executors for each worker
workflow.add_node("sales_tools", ToolNode(sales_tools))
workflow.add_node("kyc_tools", ToolNode(kyc_tools))
workflow.add_node("uw_tools", ToolNode(uw_tools))

# Define Flow
workflow.add_edge(START, "supervisor")

# Supervisor Routing Logic
workflow.add_conditional_edges(
    "supervisor",
    lambda x: x["next_agent"],
    {
        "SalesAgent": "SalesAgent",
        "KYCAgent": "KYCAgent",
        "UnderwritingAgent": "UnderwritingAgent",
        "FINISH": END
    }
)

# Worker -> Tool -> END (each turn completes after one agent responds)
# Each agent tries to use tools if needed, then ends the turn
workflow.add_conditional_edges("SalesAgent", tools_condition, {"tools": "sales_tools", END: END})
workflow.add_edge("sales_tools", "SalesAgent")

workflow.add_conditional_edges("KYCAgent", tools_condition, {"tools": "kyc_tools", END: END})
workflow.add_edge("kyc_tools", "KYCAgent")

workflow.add_conditional_edges("UnderwritingAgent", tools_condition, {"tools": "uw_tools", END: END})
workflow.add_edge("uw_tools", "UnderwritingAgent")

graph = workflow.compile(checkpointer=memory)

# === 5. Execution ===
def run_agent(user_input, thread_id):
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    # Stream values to get the final message from the last agent that spoke
    events = list(graph.stream({"messages": [HumanMessage(content=user_input)]}, config=config, stream_mode="values"))
    final_message = events[-1]["messages"][-1].content
    
    if isinstance(final_message, list): return " ".join([str(c) for c in final_message])
    return str(final_message)