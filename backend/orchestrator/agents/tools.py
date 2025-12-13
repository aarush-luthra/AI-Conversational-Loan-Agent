import os
import requests
from langchain_core.tools import tool
from services.pdf_service import PDFService
from services.db_service import DBService

pdf_service = PDFService()
db_service = DBService()

CRM_URL = "http://localhost:5001"
CREDIT_URL = "http://localhost:5002"
OFFER_URL = "http://localhost:5003"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")

# ================= SALES TOOLS =================
@tool
def get_market_rates_tool():
    """Returns current interest rate options."""
    return {"rates": [{"tenure": "12m", "rate": "10.5%"}, {"tenure": "24m", "rate": "11.0%"}]}

@tool
def check_user_history_tool(name: str):
    """Checks DB for previous loan applications."""
    return db_service.check_user_history(name)

# ================= KYC TOOLS =================
@tool
def verification_agent_tool(pan: str):
    """Verifies PAN against CRM."""
    try:
        return requests.post(f"{CRM_URL}/verify-kyc", json={"pan": pan}).json()
    except: return {"error": "CRM Down"}

# ================= UNDERWRITING TOOLS =================
@tool
def underwriting_agent_tool(amount: int, pan: str, monthly_salary: int = 0):
    """
    Calculates eligibility. 
    Requires 'pan' to fetch score/limit.
    """
    try:
        # Pass PAN to these services now!
        score_res = requests.post(f"{CREDIT_URL}/get-score", json={"pan": pan}).json()
        limit_res = requests.post(f"{OFFER_URL}/get-limit", json={"pan": pan}).json()

        score = score_res.get("credit_score", 0)
        limit = limit_res.get("pre_approved_limit", 0)

        if score < 700: return {"status": "REJECTED", "reason": f"Low Credit Score: {score}"}
        if amount <= limit: return {"status": "APPROVED", "interest": 10.5}
        
        if amount <= (2 * limit):
            if monthly_salary == 0: return {"status": "NEED_SALARY"}
            emi = (amount / 24) * 1.1 # Simple estimation
            if emi <= (0.5 * monthly_salary): return {"status": "APPROVED", "interest": 12.0}
            return {"status": "REJECTED", "reason": "EMI exceeds 50% of salary."}
            
        return {"status": "REJECTED", "reason": f"Amount > 2x Limit ({limit*2})"}
    except Exception as e: return {"error": str(e)}

@tool
def sanction_letter_tool(name: str, pan: str, amount: int, interest: float):
    """Generates and saves PDF sanction letter."""
    try:
        filename = pdf_service.generate(name, amount, interest)
        url = f"{API_BASE_URL}/static/pdfs/{filename}"
        db_service.save_loan(name, pan, amount, url)
        return {"status": "success", "link": url}
    except Exception as e: return {"error": str(e)}