import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from agents.tools import (
    check_user_history_tool, verification_agent_tool, 
    get_market_rates_tool, underwriting_agent_tool, sanction_letter_tool
)
import ast

load_dotenv()

# Setup LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))

# Define Tools List
tools = [check_user_history_tool, verification_agent_tool, get_market_rates_tool, underwriting_agent_tool, sanction_letter_tool]
llm_with_tools = llm.bind_tools(tools)

# Define State
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# MASTER AGENT PERSONA
SYSTEM_PROMPT = """You are the 'Master Agent' for Team Nexus. You orchestrate 4 worker agents: Sales, Verification, Underwriting, and Sanction.

--- CONVERSATION FLOW ---

1. **START (Memory Check)**:
    - Ask for the user's Name.
    - CALL `check_user_history_tool`.
    - If user exists: Say "Welcome back!" and ask if they want a new loan.
    - If new: Welcome them politely.

2. **SALES PHASE (Sales Agent Role)**:
    - Ask for the Loan Amount and Tenure they need.
    - Use `get_market_rates_tool` to discuss interest rates if they ask.
    - Once Amount is decided, ask for their PAN to proceed.

3. **VERIFICATION PHASE (Verification Agent)**:
    - CALL `verification_agent_tool` with their PAN.
    - If invalid, stop. If valid, confirm their name.

4. **UNDERWRITING PHASE (Underwriting Agent)**:
    - Tell the user: "I will now evaluate your eligibility."
    - CALL `underwriting_agent_tool` with the `amount`.
    - **CRITICAL LOGIC**:
        - If tool returns "APPROVED": Tell them the good news.
        - If tool returns "REJECTED": Apologize and explain the specific reason given by the tool.
        - If tool returns "NEED_SALARY": Ask the user: "Since this is a high amount, please provide your Monthly Salary."
        - When user replies (e.g., "50000"), CALL `underwriting_agent_tool` AGAIN with BOTH `amount` and `monthly_salary`.

5. **SANCTION PHASE (Sanction Agent)**:
    - If APPROVED and user says "Proceed": CALL `sanction_letter_tool`.
    - Provide the download link.

6. **END**: Thank the user.
"""

def reasoner(state: AgentState):
    msg = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    return {"messages": [llm_with_tools.invoke(msg)]}

# Graph Construction
memory = MemorySaver()
builder = StateGraph(AgentState)
builder.add_node("agent", reasoner)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
graph = builder.compile(checkpointer=memory)

# Runner
def run_agent(user_input, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the Agent
    result = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    
    # Get the raw content from the last message
    last_message = result["messages"][-1]
    raw_content = last_message.content

    # --- CLEANING LOGIC START ---
    
    # Case 1: If it's a list (Gemini sometimes returns [text, tool_call])
    if isinstance(raw_content, list):
        # Join all parts that are just text
        final_text = ""
        for part in raw_content:
            if isinstance(part, dict) and "text" in part:
                final_text += part["text"]
            elif isinstance(part, str):
                final_text += part
        return final_text.strip()

    # Case 2: If it's a String that LOOKS like a Dictionary (Your specific issue)
    # Example: "{'type': 'text', 'text': 'Hello...', 'extras': ...}"
    if isinstance(raw_content, str):
        cleaned_str = raw_content.strip()
        if cleaned_str.startswith("{") and "type" in cleaned_str:
            try:
                # Safely convert string to dict
                parsed_dict = ast.literal_eval(cleaned_str)
                # Return only the 'text' part
                return parsed_dict.get("text", raw_content)
            except:
                # If parsing fails, just return the original string
                return raw_content
    
    # Case 3: Standard Text
    return str(raw_content)