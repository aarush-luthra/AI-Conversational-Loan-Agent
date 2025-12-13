import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage, AIMessage, ToolMessage
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
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7, api_key=os.getenv("GROQ_API_KEY"))

# === 1. Define State ===
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next_agent: str
    kyc_verified: bool
    loan_amount: int
    underwriting_status: str

# === 2. Define Worker Agents (Distinct Personas & Toolsets) ===

# --- Sales Agent ---
sales_tools = [get_market_rates_tool, check_user_history_tool]
sales_llm = llm.bind_tools(sales_tools)
SALES_PROMPT = """You are an enthusiastic and persuasive Sales Agent for personal loans. Your goal is to:
1. Warmly greet the customer and build rapport
2. Understand their financial needs and convince them about the benefits of a personal loan
3. Check their history using check_user_history_tool if they provide their name
4. Discuss loan amounts, tenure options, and interest rates using get_market_rates_tool
5. Be conversational, empathetic, and persuasive like a human sales executive
6. Once the customer shows interest in a specific loan amount, inform them that we'll need to verify their details

DO NOT perform KYC verification or underwriting yourself. Hand that over by saying the customer is ready for verification."""

def sales_node(state: AgentState):
    result = sales_llm.invoke([SystemMessage(content=SALES_PROMPT)] + state["messages"])
    return {"messages": [result]}

# --- KYC Agent ---
kyc_tools = [verification_agent_tool]
kyc_llm = llm.bind_tools(kyc_tools)
KYC_PROMPT = """You are a professional Verification Officer. Your ONLY job is to:
1. Ask the customer for their PAN number for KYC verification
2. Once you receive it, use verification_agent_tool to verify it against the CRM
3. Inform the customer of the verification result
4. If verified successfully, let them know we'll proceed with credit evaluation

Be precise, professional, and security-conscious."""

def kyc_node(state: AgentState):
    result = kyc_llm.invoke([SystemMessage(content=KYC_PROMPT)] + state["messages"])
    return {"messages": [result]}

# --- Underwriting Agent ---
uw_tools = [underwriting_agent_tool, sanction_letter_tool]
uw_llm = llm.bind_tools(uw_tools)
UW_PROMPT = UW_PROMPT = """You are the Underwriting Agent. Your goal is to finalize the loan.

YOUR TOOLBOX:
1. `underwriting_agent_tool`: specific logic to Approve/Reject based on score/limit.
2. `sanction_letter_tool`: GENERATES the PDF.

STRICT PROCESS:
1. Always call `underwriting_agent_tool` first with the amount.
2. If the tool returns "APPROVED":
   - Ask the user politely: "Congratulations, you are eligible! Shall I generate your sanction letter now?"
3. If the user says "Yes" / "Proceed" / "Generate":
   - **YOU MUST CALL `sanction_letter_tool` IMMEDIATELY.**
   - Do not just say you did it. Actually trigger the tool.
   - Once the tool returns a URL, give that URL to the user.
"""

def uw_node(state: AgentState):
    result = uw_llm.invoke([SystemMessage(content=UW_PROMPT)] + state["messages"])
    return {"messages": [result]}

# === 3. Tool Execution Nodes ===
def call_tools(state: AgentState):
    """Execute tools called by agents"""
    last_message = state["messages"][-1]
    
    # Get all tools
    all_tools = sales_tools + kyc_tools + uw_tools
    tool_map = {tool.name: tool for tool in all_tools}
    
    # Execute tool calls
    tool_messages = []
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool = tool_map.get(tool_call["name"])
            if tool:
                result = tool.invoke(tool_call["args"])
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
    
    return {"messages": tool_messages}

# === 4. Routing Logic ===
def should_continue(state: AgentState):
    """Determine if we need to call tools or route to next agent"""
    last_message = state["messages"][-1]
    
    # If agent made tool calls, execute them
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Otherwise, go back to supervisor for routing
    return "supervisor"

def route_after_supervisor(state: AgentState):
    """Route to the appropriate agent based on supervisor decision"""
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "FINISH":
        return END
    return next_agent
# === 5. Master Agent (Supervisor) ===
class RouterOutput(BaseModel):
    """Structure for supervisor's decision."""
    next: Literal["SalesAgent", "KYCAgent", "UnderwritingAgent", "FINISH"]
    reasoning: str

SUPERVISOR_PROMPT = """You are the Master Agent orchestrating a loan sales process. Analyze the conversation and decide which Worker Agent should handle the next step.

**Decision Rules:**
1. **SalesAgent**: Use when:
   - Customer just joined (initial greeting)
   - Discussing loan needs, amounts, tenure, or interest rates
   - Customer needs convincing or has questions about loans
   
2. **KYCAgent**: Use when:
   - Customer has shown interest in a specific loan amount
   - Sales agent indicates customer is ready for verification
   - KYC verification is not yet completed
   
3. **UnderwritingAgent**: Use when:
   - KYC is verified successfully
   - Need to evaluate loan eligibility, credit score
   - Need to generate sanction letter
   - Customer provides salary information
   
4. **FINISH**: Use when:
   - Sanction letter has been generated and shared
   - Customer explicitly wants to end conversation
   - Loan has been rejected and customer accepts it

Analyze the last few messages and provide your reasoning before deciding."""

supervisor_llm = llm.with_structured_output(RouterOutput)

def supervisor_node(state: AgentState):
    """Master Agent decides which worker agent should act next"""
    result = supervisor_llm.invoke([SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"])
    print(f"[SUPERVISOR] Routing to: {result.next} | Reason: {result.reasoning}")
    return {"next_agent": result.next}

# === 6. Build the Graph ===
memory = MemorySaver()
workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("SalesAgent", sales_node)
workflow.add_node("KYCAgent", kyc_node)
workflow.add_node("UnderwritingAgent", uw_node)
workflow.add_node("tools", call_tools)

# Define the flow - Start with sales agent for first message
workflow.add_edge(START, "SalesAgent")

# After agents respond, check if they need tools
def route_after_agent(state: AgentState):
    """After an agent responds, check if tools are needed"""
    last_message = state["messages"][-1]
    
    # If agent wants to call tools, go to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Otherwise we're done with this turn - return response to user
    return END

workflow.add_conditional_edges("SalesAgent", route_after_agent, {
    "tools": "tools",
    END: END
})
workflow.add_conditional_edges("KYCAgent", route_after_agent, {
    "tools": "tools",
    END: END
})
workflow.add_conditional_edges("UnderwritingAgent", route_after_agent, {
    "tools": "tools",
    END: END
})

# After tools execute, return to the SAME agent to formulate response
def route_after_tools(state: AgentState):
    """After tools run, go back to agent to formulate response with tool results"""
    messages = state["messages"]
    # Find which agent made the tool call by looking backwards
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            # Check the agent based on the last supervisor decision
            next_agent = state.get("next_agent", "SalesAgent")
            return next_agent
    return "SalesAgent"

workflow.add_conditional_edges("tools", route_after_tools, {
    "SalesAgent": "SalesAgent",
    "KYCAgent": "KYCAgent",
    "UnderwritingAgent": "UnderwritingAgent"
})

# Supervisor routes to appropriate agent or END
workflow.add_conditional_edges("supervisor", route_after_supervisor, {
    "SalesAgent": "SalesAgent",
    "KYCAgent": "KYCAgent",
    "UnderwritingAgent": "UnderwritingAgent",
    END: END
})

graph = workflow.compile(checkpointer=memory)

# === 7. Execution ===
def run_agent(user_input, thread_id):
    """Execute the agentic workflow for a user message"""
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
    
    try:
        # Stream through the graph
        events = []
        for event in graph.stream(
            {"messages": [HumanMessage(content=user_input)]}, 
            config=config, 
            stream_mode="values"
        ):
            events.append(event)
        
        # Get the last AI message
        if events:
            for msg in reversed(events[-1]["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    return str(msg.content)
        
        return "I apologize, but I'm having trouble processing your request. Could you please try again?"
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return f"I encountered an error: {str(e)}. Please try again."