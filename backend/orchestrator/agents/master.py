import os
import re
import json
import logging
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage, AIMessage, ToolMessage
from typing import Annotated, TypedDict, Literal, Optional
from langgraph.graph.message import add_messages
from pydantic import BaseModel

# Import tools
from agents.tools import (
    get_market_rates_tool, check_user_history_tool,
    verification_agent_tool,
    underwriting_agent_tool, sanction_letter_tool
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- FIX START: ABSOLUTE PATH ---
# We use the absolute path to guarantee the .env file is found.
env_path = Path("/Users/anika/Documents/PROJECTS/AI-Conversational-Loan-Agent/.env")

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"OPENAI_API_KEY loaded successfully from: {env_path}")
else:
    logger.error(f"CRITICAL: .env file NOT found at: {env_path}")
# --- FIX END ---

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",  # or "gpt-4o" for GPT-4
    temperature=0.3,      # Lower temperature for professional, consistent responses
    api_key=os.getenv("OPENAI_API_KEY"),
    streaming=True        # Enable streaming
)

# ================= STATE DEFINITION =================
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next_agent: str
    
    # Customer Information
    customer_name: Optional[str]
    pan_number: Optional[str]
    phone_number: Optional[str]
    
    # Loan Details
    loan_amount: Optional[int]
    requested_tenure: Optional[str]
    monthly_salary: Optional[int]
    
    # Process Status
    kyc_verified: bool
    credit_score: Optional[int]
    pre_approved_limit: Optional[int]
    underwriting_status: str  # PENDING, APPROVED, REJECTED, NEED_SALARY
    approved_interest_rate: Optional[float]
    sanction_letter_url: Optional[str]

# ================= HELPER FUNCTIONS =================
def extract_loan_amount(text: str) -> Optional[int]:
    """Extract loan amount from text (handles lakhs, thousands, etc.)"""
    text = text.lower()
    
    # Pattern: X lakh/lakhs
    lakh_match = re.search(r'(\d+\.?\d*)\s*(?:lakh|lac)', text)
    if lakh_match:
        return int(float(lakh_match.group(1)) * 100000)
    
    # Pattern: X thousand
    thousand_match = re.search(r'(\d+\.?\d*)\s*thousand', text)
    if thousand_match:
        return int(float(thousand_match.group(1)) * 1000)
    
    # Pattern: ₹X or Rs X (direct numbers)
    rupee_match = re.search(r'[₹rs]\s*(\d+(?:,\d+)*)', text)
    if rupee_match:
        return int(rupee_match.group(1).replace(',', ''))
    
    # Pattern: plain large numbers (> 10000)
    number_match = re.search(r'\b(\d{5,})\b', text)
    if number_match:
        return int(number_match.group(1))
    
    return None

def extract_salary(text: str) -> Optional[int]:
    """Extract monthly salary from text"""
    text = text.lower()
    
    # Pattern: X thousand per month
    if 'thousand' in text:
        match = re.search(r'(\d+\.?\d*)\s*thousand', text)
        if match:
            return int(float(match.group(1)) * 1000)
    
    # Pattern: ₹X or Rs X
    match = re.search(r'[₹rs]\s*(\d+(?:,\d+)*)', text)
    if match:
        return int(match.group(1).replace(',', ''))
    
    # Pattern: plain numbers between 10k-500k (reasonable salary range)
    match = re.search(r'\b(\d{5,6})\b', text)
    if match:
        salary = int(match.group(1))
        if 10000 <= salary <= 500000:
            return salary
    
    return None

def extract_pan(text: str) -> Optional[str]:
    """Extract PAN number from text"""
    # PAN format: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)
    match = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text.upper())
    return match.group(1) if match else None

def validate_pan(pan: str) -> dict:
    """Validate PAN number format using code-based validation.
    
    PAN Format: [A-Z]{5}[0-9]{4}[A-Z]
    - First 5 characters: Uppercase letters
    - Next 4 characters: Digits
    - Last character: Uppercase letter
    
    Args:
        pan: The PAN number to validate
        
    Returns:
        dict: {"valid": bool, "error": str | None, "pan": str | None}
    """
    if not pan:
        return {"valid": False, "error": "PAN number is required", "pan": None}
    
    # Normalize: remove spaces and convert to uppercase
    pan = pan.strip().upper()
    
    # Check length
    if len(pan) != 10:
        return {
            "valid": False, 
            "error": f"PAN must be exactly 10 characters (got {len(pan)})",
            "pan": None
        }
    
    # Validate format with regex: [A-Z]{5}[0-9]{4}[A-Z]
    pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
    if not re.match(pan_pattern, pan):
        return {
            "valid": False,
            "error": "Invalid PAN format. Expected: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)",
            "pan": None
        }
    
    # Additional validation: 4th character indicates holder type
    # P = Individual, C = Company, H = HUF, A = AOP, B = BOI, etc.
    holder_type = pan[3]
    valid_holder_types = ['P', 'C', 'H', 'A', 'B', 'G', 'J', 'L', 'F', 'T']
    if holder_type not in valid_holder_types:
        logger.warning(f"Unusual PAN holder type: {holder_type}")
    
    logger.info(f"PAN validated successfully: {pan[:4]}****{pan[-2:]}")
    return {"valid": True, "error": None, "pan": pan}

# ================= WORKER AGENTS =================

# --- Sales Agent ---
sales_tools = [get_market_rates_tool, check_user_history_tool]
sales_llm = llm.bind_tools(sales_tools)

SALES_PROMPT = """You are Nexus, an enthusiastic and empathetic Personal Loan Advisor. Your goal is to build rapport and understand customer needs.

**Your Responsibilities:**
1. Warmly greet new customers and introduce yourself
2. Ask about their financial needs and loan requirements
3. If they mention their name, use check_user_history_tool to see if they're an existing customer
4. Discuss loan amounts, tenure options (12/24/36 months)
5. Use get_market_rates_tool to show interest rate options
6. Be conversational, helpful, and build trust

**Key Guidelines:**
- Extract loan amount when customer mentions it (e.g., "I need 5 lakhs")
- Ask clarifying questions: "What's the loan for?", "What tenure works best for you?"
- Once customer confirms their desired amount, say: "Excellent! Let me connect you with our verification team to proceed with your application."
- Be positive and encouraging
- Don't perform KYC or credit checks yourself

**Current Context:**
- Customer Name: {customer_name}
- Requested Amount: {loan_amount}
- KYC Status: {kyc_status}

Remember: You're building trust and gathering initial requirements. Keep it conversational!"""

def sales_node(state: AgentState):
    logger.info("=== SALES AGENT ACTIVATED ===")
    
    # Build context-aware prompt
    prompt = SALES_PROMPT.format(
        customer_name=state.get("customer_name") or "Not provided yet",
        loan_amount=f"₹{state.get('loan_amount'):,}" if state.get("loan_amount") else "Not specified yet",
        kyc_status="Completed ✓" if state.get("kyc_verified") else "Pending"
    )
    
    result = sales_llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    
    # Extract information from conversation
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break
    
    updates = {"messages": [result]}
    
    # Extract loan amount
    if not state.get("loan_amount"):
        amount = extract_loan_amount(last_user_msg)
        if amount:
            updates["loan_amount"] = amount
            logger.info(f"Extracted loan amount: ₹{amount:,}")
    
    # Extract customer name from conversation
    if not state.get("customer_name"):
        # Simple name extraction (you can enhance this)
        if any(word in last_user_msg.lower() for word in ["my name is", "i am", "i'm"]):
            words = last_user_msg.split()
            for i, word in enumerate(words):
                if word.lower() in ["is", "am"] and i + 1 < len(words):
                    name = words[i + 1].strip('.,!?').title()
                    if len(name) > 2:
                        updates["customer_name"] = name
                        logger.info(f"Extracted customer name: {name}")
                        break
    
    return updates

# --- KYC Agent ---
kyc_tools = [verification_agent_tool]
kyc_llm = llm.bind_tools(kyc_tools)

KYC_PROMPT = """You are Priya, a professional KYC Verification Officer. Your role is to verify customer identity securely.

**Your Responsibilities:**
1. If KYC is already verified, politely inform and hand over to underwriting
2. Ask customer for their PAN number (10-character alphanumeric)
3. Once received, use verification_agent_tool to verify against CRM
4. Inform customer of verification result clearly

**Key Guidelines:**
- Be professional, security-conscious, and respectful
- Validate PAN format: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)
- After successful verification, say: "Thank you! Your details are verified. Let me connect you to our credit evaluation team."
- If verification fails, politely ask them to check PAN and retry

**Current Context:**
- Customer Name: {customer_name}
- KYC Status: {kyc_status}
- Loan Amount: {loan_amount}

Keep it brief and professional!"""

def kyc_node(state: AgentState):
    logger.info("=== KYC AGENT ACTIVATED ===")

    # If already verified
    if state.get("kyc_verified"):
        return {
            "messages": [
                AIMessage(
                    content="✅ Your KYC is already verified. Let me connect you with our credit evaluation team."
                )
            ]
        }

    # Get last user message
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    # Try extracting PAN
    extracted_pan = extract_pan(last_user_msg)

    if not extracted_pan:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "To proceed, please share your **PAN number**.\n\n"
                        "📌 Format: **ABCDE1234F**\n"
                        "(5 letters, 4 digits, 1 letter)"
                    )
                )
            ]
        }

    # Validate PAN using code (NO TOOL, NO LLM)
    validation = validate_pan(extracted_pan)

    if not validation["valid"]:
        return {
            "messages": [
                AIMessage(
                    content=(
                        f"❌ **Invalid PAN**: {validation['error']}\n\n"
                        "Please re-enter your PAN in this format: **ABCDE1234F**"
                    )
                )
            ]
        }

    # ✅ PAN is valid → mark KYC verified
    logger.info(f"PAN VERIFIED (CODE-BASED): {validation['pan']}")

    return {
        "pan_number": validation["pan"],
        "kyc_verified": True,
        "messages": [
            AIMessage(
                content=(
                    "✅ **KYC Successful!**\n\n"
                    "Your PAN has been verified successfully.\n"
                    "I’ll now connect you with our credit evaluation team to assess your loan eligibility."
                )
            )
        ]
    }



# --- Underwriting Agent ---
uw_tools = [underwriting_agent_tool, sanction_letter_tool]
uw_llm = llm.bind_tools(uw_tools)

UW_PROMPT = """You are Dr. Sharma, a Senior Credit Analyst. Your role is to evaluate loan eligibility fairly and transparently.

**Your Responsibilities:**
1. Use underwriting_agent_tool to assess loan eligibility
2. Handle three outcomes:
   - **APPROVED**: Congratulate customer, explain terms, offer to generate sanction letter
   - **NEED_SALARY**: Request monthly salary (in-hand amount), then re-evaluate
   - **REJECTED**: Explain reason empathetically, suggest alternatives
3. If approved and customer confirms, use sanction_letter_tool to generate PDF

**Key Guidelines:**
- Always explain decisions clearly and transparently
- For NEED_SALARY: Ask "Could you please share your monthly in-hand salary?"
- Extract salary from customer response and call underwriting_agent_tool again
- For rejections: Be empathetic, provide actionable suggestions
- For approvals: Clearly state loan amount, interest rate, and next steps
- **CRITICAL**: When calling underwriting_agent_tool, you MUST pass the PAN number: {pan_number}
- **CRITICAL**: When calling sanction_letter_tool after approval:
  * Use the CUSTOMER'S REQUESTED loan amount: {loan_amount}
  * Use the customer's name: {customer_name}
  * Use the PAN: {pan_number}
  * Use the approved interest rate from underwriting result
  * After generation, ALWAYS include the download link in your response with markdown format:
    "Your sanction letter is ready! [Download Sanction Letter](DOWNLOAD_LINK_HERE)"

**Current Context:**
- Customer Name: {customer_name}
- PAN: {pan_number}
- Loan Amount: {loan_amount}
- Monthly Salary: {monthly_salary}
- Credit Score: {credit_score}
- Underwriting Status: {underwriting_status}

Be professional, transparent, and helpful!"""

def uw_node(state: AgentState):
    logger.info("=== UNDERWRITING AGENT ACTIVATED ===")

    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    updates = {}

    # ✅ Extract UPDATED loan amount (CRITICAL FIX)
    amount = extract_loan_amount(last_user_msg)
    if amount:
        updates["loan_amount"] = amount
        logger.info(f"Updated loan amount: ₹{amount:,}")

    # Extract salary
    salary = extract_salary(last_user_msg)
    if salary:
        updates["monthly_salary"] = salary
        logger.info(f"Extracted monthly salary: ₹{salary:,}")

    # Build prompt AFTER updates
    prompt = UW_PROMPT.format(
        customer_name=state.get("customer_name") or "Customer",
        pan_number=state.get("pan_number") or "Not provided",
        loan_amount=f"₹{updates.get('loan_amount', state.get('loan_amount')):,}"
        if updates.get("loan_amount") or state.get("loan_amount")
        else "Not specified",
        monthly_salary=f"₹{updates.get('monthly_salary', state.get('monthly_salary')):,}"
        if updates.get("monthly_salary") or state.get("monthly_salary")
        else "Not provided",
        credit_score=state.get("credit_score") or "Pending",
        underwriting_status=state.get("underwriting_status", "PENDING"),
    )

    result = uw_llm.invoke([SystemMessage(content=prompt)] + state["messages"])

    updates["messages"] = [result]
    return updates

# ================= TOOL EXECUTION =================
def call_tools(state: AgentState):
    """Execute tools and update state based on results"""
    logger.info("=== EXECUTING TOOLS ===")
    last_message = state["messages"][-1]
    
    all_tools = sales_tools + kyc_tools + uw_tools
    tool_map = {tool.name: tool for tool in all_tools}
    
    tool_messages = []
    state_updates = {}
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
            
            tool = tool_map.get(tool_name)
            if tool:
                try:
                    result = tool.invoke(tool_args)
                    tool_messages.append(
                        ToolMessage(content=json.dumps(result, indent=2), tool_call_id=tool_call["id"])
                    )
                    
                    # Update state based on tool results
                    if tool_name == "verification_agent_tool":
                        if result.get("verified"):
                            state_updates["kyc_verified"] = True
                            state_updates["customer_name"] = result.get("name", state.get("customer_name"))
                            state_updates["pan_number"] = result.get("pan", state.get("pan_number"))
                            state_updates["phone_number"] = result.get("phone")
                            logger.info(f"KYC VERIFIED for {result.get('name')}")
                    
                    elif tool_name == "underwriting_agent_tool":
                        status = result.get("status")
                        state_updates["underwriting_status"] = status
                        
                        if status == "APPROVED":
                            state_updates["approved_interest_rate"] = result.get("interest_rate")
                            state_updates["credit_score"] = result.get("credit_score")
                            logger.info(f"LOAN APPROVED: {result}")
                        
                        elif status == "REJECTED":
                            state_updates["credit_score"] = result.get("credit_score")
                            logger.info(f"LOAN REJECTED: {result.get('reason')}")
                        
                        elif status == "NEED_SALARY":
                            state_updates["credit_score"] = result.get("credit_score")
                            state_updates["pre_approved_limit"] = result.get("pre_approved_limit")
                            logger.info("NEED_SALARY status - awaiting salary info")
                    
                    elif tool_name == "sanction_letter_tool":
                        if result.get("status") == "success":
                            state_updates["sanction_letter_url"] = result.get("download_link")
                            logger.info(f"Sanction letter generated: {result.get('download_link')}")
                    
                except Exception as e:
                    logger.error(f"Tool execution error: {str(e)}")
                    tool_messages.append(
                        ToolMessage(
                            content=json.dumps({"error": str(e)}),
                            tool_call_id=tool_call["id"]
                        )
                    )
    
    return {"messages": tool_messages, **state_updates}

# ================= SUPERVISOR (MASTER AGENT) =================
class RouterOutput(BaseModel):
    next: Literal["SalesAgent", "KYCAgent", "UnderwritingAgent", "FINISH"]
    reasoning: str

SUPERVISOR_PROMPT = """You are the Master Orchestrator for a loan application system. Analyze the conversation and current state to route to the appropriate agent.

**Current State:**
- Customer Name: {customer_name}
- Loan Amount: {loan_amount}
- KYC Verified: {kyc_verified}
- Underwriting Status: {underwriting_status}
- Sanction Letter: {sanction_letter}

**Routing Rules (FOLLOW EXACTLY IN THIS PRIORITY ORDER):**

**PRIORITY 1 - Check Sanction Letter Status:**
- IF underwriting_status is "APPROVED" AND sanction_letter is "Not generated" AND customer wants/confirms letter
  → Route to **UnderwritingAgent** (to generate the letter)
- IF sanction_letter is "Generated ✓"
  → Route to **FINISH** (letter already exists)

**PRIORITY 2 - Check Underwriting Status:**
- IF kyc_verified is "Yes ✓" AND underwriting_status is "PENDING"
  → Route to **UnderwritingAgent** (to evaluate eligibility)
- IF underwriting_status is "NEED_SALARY" AND customer provided salary
  → Route to **UnderwritingAgent** (to re-evaluate with salary)
- IF underwriting_status is "REJECTED" AND customer acknowledged
  → Route to **FINISH**

**PRIORITY 3 - Check KYC Status:**
- IF kyc_verified is "No ✗" AND customer ready to verify
  → Route to **KYCAgent**

**PRIORITY 4 - Default:**
- IF loan_amount is "Not specified" OR initial conversation
  → Route to **SalesAgent**

**CRITICAL RULES:**
- **NEVER** route to FINISH if sanction_letter is "Not generated" and customer wants it
- **ALWAYS** route to UnderwritingAgent if APPROVED + Not generated + customer confirms
- Check state variables FIRST before reading conversation context

Provide clear reasoning for your decision."""

supervisor_llm = llm.with_structured_output(RouterOutput)

def supervisor_node(state: AgentState):
    """Master agent decides routing based on conversation and state"""
    logger.info("=== SUPERVISOR ROUTING ===")
    
    # Build context-aware prompt
    prompt = SUPERVISOR_PROMPT.format(
        customer_name=state.get("customer_name") or "Not provided",
        loan_amount=f"₹{state.get('loan_amount'):,}" if state.get("loan_amount") else "Not specified",
        kyc_verified="Yes ✓" if state.get("kyc_verified") else "No ✗",
        underwriting_status=state.get("underwriting_status", "PENDING"),
        sanction_letter="Generated ✓" if state.get("sanction_letter_url") else "Not generated"
    )
    
    # Get last few messages for context
    recent_messages = state["messages"][-6:] if len(state["messages"]) > 6 else state["messages"]
    
    result = supervisor_llm.invoke([SystemMessage(content=prompt)] + recent_messages)
    
    logger.info(f"ROUTING DECISION: {result.next}")
    logger.info(f"REASONING: {result.reasoning}")
    
    return {"next_agent": result.next}

# ================= GRAPH CONSTRUCTION =================
def build_graph():
    """Construct the LangGraph workflow"""
    memory = MemorySaver()
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("SalesAgent", sales_node)
    workflow.add_node("KYCAgent", kyc_node)
    workflow.add_node("UnderwritingAgent", uw_node)
    workflow.add_node("tools", call_tools)
    
    # Start with supervisor
    workflow.add_edge(START, "supervisor")
    
    # Supervisor routes to agents or END
    def route_from_supervisor(state: AgentState):
        next_agent = state.get("next_agent", "SalesAgent")
        if next_agent == "FINISH":
            return END
        return next_agent
    
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "SalesAgent": "SalesAgent",
            "KYCAgent": "KYCAgent",
            "UnderwritingAgent": "UnderwritingAgent",
            END: END
        }
    )
    
    # Agents check if tools needed, otherwise return to supervisor
    def route_from_agent(state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END  # Return response to user
    
    workflow.add_conditional_edges("SalesAgent", route_from_agent, {"tools": "tools", END: END})
    workflow.add_conditional_edges("KYCAgent", route_from_agent, {"tools": "tools", END: END})
    workflow.add_conditional_edges("UnderwritingAgent", route_from_agent, {"tools": "tools", END: END})
    
    # After tools execute, return to same agent to formulate response
    def route_from_tools(state: AgentState):
        # Determine which agent called the tool
        messages = state["messages"]
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                # Use state to determine active agent
                next_agent = state.get("next_agent", "SalesAgent")
                logger.info(f"Returning to {next_agent} after tool execution")
                return next_agent
        return "SalesAgent"
    
    workflow.add_conditional_edges(
        "tools",
        route_from_tools,
        {
            "SalesAgent": "SalesAgent",
            "KYCAgent": "KYCAgent",
            "UnderwritingAgent": "UnderwritingAgent"
        }
    )
    
    return workflow.compile(checkpointer=memory)

# Build the graph
graph = build_graph()

# ================= EXECUTION =================
def run_agent(user_input: str, thread_id: str):
    """Execute the agentic workflow for a user message (non-streaming)"""
    logger.info(f"\n{'='*60}")
    logger.info(f"USER INPUT: {user_input}")
    logger.info(f"THREAD ID: {thread_id}")
    logger.info(f"{'='*60}\n")
    
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    
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
            final_state = events[-1]
            
            # Log final state
            logger.info(f"\n{'='*60}")
            logger.info("FINAL STATE:")
            logger.info(f"Customer: {final_state.get('customer_name')}")
            logger.info(f"Loan Amount: {final_state.get('loan_amount')}")
            logger.info(f"KYC Verified: {final_state.get('kyc_verified')}")
            logger.info(f"Underwriting: {final_state.get('underwriting_status')}")
            logger.info(f"{'='*60}\n")
            
            # Find last AI message
            for msg in reversed(final_state["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    return str(msg.content)
        
        return "I apologize, but I'm having trouble processing your request. Could you please try again?"
    
    except Exception as e:
        logger.error(f"ERROR in run_agent: {str(e)}", exc_info=True)
        return f"I encountered an error: {str(e)}. Please try again or contact support."


def run_agent_stream(user_input: str, thread_id: str):
    """Execute the agentic workflow with streaming response.
    
    This generator yields response chunks as they become available,
    enabling real-time streaming to the frontend.
    
    Args:
        user_input: The user's message
        thread_id: Session/thread identifier
        
    Yields:
        str: Response chunks as they stream in
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"[STREAMING] USER INPUT: {user_input}")
    logger.info(f"[STREAMING] THREAD ID: {thread_id}")
    logger.info(f"{'='*60}\n")
    
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    
    try:
        final_response = ""
        
        # Stream through the graph with updates mode for token-level streaming
        for event in graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="updates"
        ):
            # Process each update event
            for node_name, node_output in event.items():
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage) and msg.content:
                            # Yield the content chunk
                            content = str(msg.content)
                            if content and content != final_response:
                                # Only yield new content
                                new_content = content[len(final_response):] if content.startswith(final_response) else content
                                if new_content:
                                    yield new_content
                                    final_response = content
        
        # If no response was streamed, yield error message
        if not final_response:
            yield "I apologize, but I'm having trouble processing your request. Could you please try again?"
            
    except Exception as e:
        logger.error(f"ERROR in run_agent_stream: {str(e)}", exc_info=True)
        yield f"I encountered an error: {str(e)}. Please try again or contact support."