import os
import requests
from langchain_core.tools import tool
from services.pdf_service import PDFService
from services.db_service import DBService

# Initialize Services
pdf_service = PDFService()
db_service = DBService()

# API Config
CRM_URL = "http://localhost:5001"
CREDIT_URL = "http://localhost:5002"
OFFER_URL = "http://localhost:5003"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")

# --- 1. MEMORY AGENT ---
@tool
def check_user_history_tool(name: str):
    """Checks if the user has applied before."""
    return db_service.check_user_history(name)

# --- 2. VERIFICATION AGENT ---
@tool
def verification_agent_tool(pan: str):
    """Verifies KYC details against the CRM."""
    try:
        return requests.post(f"{CRM_URL}/verify-kyc", json={"pan": pan}).json()
    except: return {"error": "CRM Unavailable"}

# --- 3. SALES AGENT (Helper) ---
@tool
def get_market_rates_tool():
    """Returns current interest rates for negotiation."""
    return {"base_rate": "10.5%", "tenure_options": ["12 months", "24 months", "36 months"]}

# --- 4. UNDERWRITING AGENT (The Brain) ---
@tool
def underwriting_agent_tool(amount: int, monthly_salary: int = 0):
    """
    Evaluates loan eligibility.
    input: amount (requested loan), monthly_salary (optional, send 0 if unknown).
    """
    try:
        # Step A: Get Credit Score
        score_res = requests.post(f"{CREDIT_URL}/get-score").json()
        score = score_res.get("credit_score", 0)

        # Step B: Get Pre-Approved Limit
        limit_res = requests.post(f"{OFFER_URL}/get-limit").json()
        limit = limit_res.get("pre_approved_limit", 200000)

        # --- LOGIC GATES ---
        
        # Gate 1: Credit Score Check
        if score < 700:
            return {"status": "REJECTED", "reason": f"Credit Score {score} is below 700."}

        # Gate 2: Instant Approval (Amount <= Limit)
        if amount <= limit:
            return {"status": "APPROVED", "amount": amount, "interest": 10.5, "reason": "Within pre-approved limit."}

        # Gate 3: High Value Loan (Limit < Amount <= 2x Limit)
        if amount <= (2 * limit):
            # Check if salary was provided
            if monthly_salary == 0:
                return {"status": "NEED_SALARY", "reason": "Amount exceeds pre-approved limit. Please ask user for Monthly Salary."}
            
            # EMI Calculation (Simplified: 10% interest for 24 months)
            # EMI formula roughly: (P * R * (1+R)^N) / ((1+R)^N - 1)
            # Approximation for hackathon: EMI = Amount / 24 * 1.1
            estimated_emi = (amount / 24) * 1.1
            
            if estimated_emi <= (0.5 * monthly_salary):
                return {"status": "APPROVED", "amount": amount, "interest": 12.0, "reason": "Salary supports the EMI."}
            else:
                return {"status": "REJECTED", "reason": f"EMI ({int(estimated_emi)}) is > 50% of Salary ({monthly_salary})."}

        # Gate 4: Too High (> 2x Limit)
        return {"status": "REJECTED", "reason": f"Requested amount {amount} exceeds 2x Pre-Approved limit ({limit*2})."}

    except Exception as e:
        return {"error": str(e)}

# --- 5. SANCTION AGENT ---
@tool
def sanction_letter_tool(name: str, pan: str, amount: int, interest: float):
    """Generates PDF. Call ONLY if status is APPROVED."""
    try:
        filename = pdf_service.generate(name, amount, interest)
        url = f"{API_BASE_URL}/static/pdfs/{filename}"
        db_service.save_loan(name, pan, amount, url)
        return {"status": "success", "download_link": url}
    except Exception as e:
        return {"error": str(e)}