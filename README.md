# Team Nexus: AI Conversational Loan Agent

### EY Techathon 6.0 (BFSI Track)

**Team Nexus** presents an AI-driven conversational chatbot designed to automate the end-to-end personal loan origination process for Non-Banking Financial Companies (NBFCs). This solution replaces manual sales processes with an intelligent 24/7 AI agent system to increase conversion rates and operational efficiency.

Built with **LangGraph + OpenAI GPT-4o-mini** for intelligent loan processing with payslip OCR and automated KYC verification.

-----

## 1. The Challenge

  * **Problem:** The existing manual process for upselling personal loans is inefficient, costly, and creates operational bottlenecks, slowing growth.
  * **Solution:** A conversational AI built on a **Unified Single-Agent Architecture**. A central intelligent agent handles the entire customer journey—from loan inquiry through KYC verification, underwriting, salary verification via payslip OCR, and final approval with automated sanction letter generation.

-----

## 2. System Architecture

### A. Backend: The "Brain" (Orchestrator)

  * Built with **Python + Flask**, hosting a **LangGraph** unified agent state machine
  * Uses **OpenAI API (GPT-4o-mini)** as the LLM engine for intelligent, conversational responses
  * Single agent orchestrates all workflow stages: Sales → Salary Verification → KYC → Underwriting → Sanction
  * **Payslip OCR Integration**: Uses Tesseract-OCR + pdf2image to automatically extract salary from uploaded payslips

### B. Key Features

1. **Smart Salary Verification:**
   - Accepts payslip uploads (PDF/PNG/JPG)
   - Automatic OCR extraction of monthly salary
   - Asks for payslip confirmation if user types salary without uploading
   - Validates salary against 2x loan rule (salary × 24 months ≥ 2 × loan amount)

2. **Intelligent KYC Verification:**
   - PAN number validation
   - Integration with mock CRM service for customer verification
   - Tracks KYC status throughout conversation

3. **Loan Eligibility Assessment:**
   - 2x salary rule validation
   - EMI must be ≤ 50% of monthly salary
   - Credit score check (via mock credit bureau)
   - Pre-approved limit validation (via mock offer mart)

4. **Automated Sanction Letter:**
   - PDF generation for approved loans
   - Downloadable directly from chat interface
   - Includes loan terms, interest rates, EMI, and tenure

### C. Mocked Bank Infrastructure

Three independent Flask microservices run separately to simulate real banking APIs:

  * **Mock CRM Server (Port 5001):** Responds to KYC/PAN validation requests
  * **Mock Credit Bureau (Port 5002):** Provides dummy credit scores (650-850)
  * **Mock Offer Mart (Port 5003):** Provides pre-approved loan limits

-----

## 3. 📁 Project Structure

```text
AI-Conversational-Loan-Agent/
├── backend/
│   ├── mock_services/
│   │   ├── crm.py                  # Mock CRM (Port 5001)
│   │   ├── credit_bureau.py        # Mock Credit Bureau (Port 5002)
│   │   └── offer_mart.py           # Mock Offer Mart (Port 5003)
│   │
│   ├── orchestrator/
│   │   ├── agents/
│   │   │   ├── unified_agent.py    # Single unified agent handling entire workflow
│   │   │   └── tools.py            # KYC, underwriting, and sanction letter tools
│   │   │
│   │   ├── services/
│   │   │   ├── db_service.py       # SQLite database manager
│   │   │   └── pdf_service.py      # PDF generation for sanction letters
│   │   │
│   │   ├── static/
│   │   │   ├── pdfs/               # Generated sanction letter PDFs
│   │   │   └── uploads/            # User-uploaded payslips (temporary)
│   │   │
│   │   └── app.py                  # Main Flask application (Port 5000)
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── index.html                  # Chat interface
│   ├── style.css                   # Responsive styling
│   └── script.js                   # Chat logic and API integration
│
├── .env                            # Environment variables (OpenAI API key)
├── README.md                       # This file
└── INSTALL_TESSERACT.md           # Tesseract-OCR installation guide
```

-----

## 4. Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript, Marked.js | Responsive web chat with Markdown rendering |
| **Backend** | Python 3.9+, Flask, Flask-CORS | REST API orchestration |
| **AI** | LangChain, LangGraph, OpenAI GPT-4o-mini | Unified agent for intelligent processing |
| **OCR** | Tesseract-OCR, pdf2image, pdfplumber, pytesseract | Payslip analysis and salary extraction |
| **Database** | SQLite | User data and loan application logs |
| **PDF Generation** | ReportLab | Sanction letter creation |
| **Mock Services** | Flask microservices | CRM, Credit Bureau, Offer Mart APIs |

-----

## 5. 🚀 Quick Start Guide

### Prerequisites

- Python 3.9+
- OpenAI API Key
- Tesseract-OCR installed (see INSTALL_TESSERACT.md)
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/HR-coding/AI-Conversational-Loan-Agent.git
cd AI-Conversational-Loan-Agent
```

### Step 2: Set Up Environment

Create `.env` in project root:

```bash
OPENAI_API_KEY="sk-proj-..."
```

### Step 3: Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 4: Start All Services

**Terminal 1 - CRM Service:**
```bash
cd backend/mock_services
python crm.py
```

**Terminal 2 - Credit Bureau:**
```bash
cd backend/mock_services
python credit_bureau.py
```

**Terminal 3 - Offer Mart:**
```bash
cd backend/mock_services
python offer_mart.py
```

**Terminal 4 - Main Backend:**
```bash
cd backend/orchestrator
python app.py
```

Backend runs on: `http://127.0.0.1:5000`

### Step 5: Open Frontend

Navigate to `http://127.0.0.1:5000` in your browser.

### Step 6: Test the System

Sample test with PAN: `ABCDE1000F`

1. Ask: "I need a loan for ₹70,000"
2. Upload payslip (use sample_payslip.png)
3. Provide PAN when asked
4. System evaluates and approves/rejects
5. Download sanction letter if approved

-----

## 6. 🔑 Key Features

✅ **Payslip OCR** - Automatic salary extraction from uploaded payslips  
✅ **Smart Salary Verification** - Asks for payslip if user only types salary  
✅ **2x Salary Rule** - Validates loan amount against eligible limit  
✅ **EMI Validation** - Ensures EMI ≤ 50% of monthly salary  
✅ **PAN Verification** - Real-time KYC validation via mock CRM  
✅ **Credit Score Check** - Evaluates creditworthiness  
✅ **Sanction Letter** - Auto-generated PDF for approved loans  
✅ **Responsive UI** - Mobile-friendly chat interface  
✅ **Markdown Support** - Rich text responses with formatting  
✅ **RBI Compliant** - Audit trail via SQLite logs  

-----

## 7. Important Notes

### Tesseract-OCR Setup

On **Windows**: Must install separately. See [INSTALL_TESSERACT.md](INSTALL_TESSERACT.md)

Expected path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### Poppler for PDF Processing

Download from: https://github.com/oschwartz10612/poppler-windows/releases/

Expected path: `C:\Users\[USERNAME]\poppler\poppler-24.08.0\Library\bin`

### Mock Service Databases

First run creates `mock_bank.db` with 1005 test customers.  
Test PAN: `ABCDE1000F` through `ABCDE5000F`

### CORS Configuration

Frontend serves from Flask at `http://127.0.0.1:5000`  
API endpoint: `http://127.0.0.1:5000/chat`

-----

## 8. API Reference

### POST /chat

Send a message to the agent

**Request:**
```json
{
  "message": "I need a loan for 20000",
  "session_id": "demo_user"
}
```

**With File Upload:**
```
FormData:
- message: "I'm uploading my payslip"
- session_id: "demo_user"
- file: <payslip.png>
```

**Response:**
```json
{
  "response": "Thank you for uploading your payslip! I can see your monthly salary is ₹70,000..."
}
```

-----

## 9. Troubleshooting

| Issue | Solution |
| --- | --- |
| "Module not found" | Run: `pip install -r backend/requirements.txt` |
| OCR not working | Install Tesseract following INSTALL_TESSERACT.md |
| Backend not responding | Ensure all 4 services running on correct ports |
| CORS errors | Check Flask-CORS enabled in app.py |
| Mock services disconnected | Restart services and backend |
| Blank screen after upload | Hard refresh browser (Ctrl+Shift+R) |

-----

## 10. Team

**EY Techathon 6.0 - Team Nexus**

Built with ❤️ for the BFSI Track
