# System Architecture

## Overview

The AI Conversational Loan Agent uses a **unified single-agent architecture** powered by LangGraph and OpenAI GPT-4o-mini to handle the complete loan origination workflow in a conversational manner.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React/Browser)              │
│  - Chat Interface (HTML/CSS/JS)                            │
│  - File Upload (Payslips)                                  │
│  - Message Display with Markdown                           │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Flask Backend (Port 5000)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /chat API Endpoint                                  │  │
│  │  - Receives messages & files                         │  │
│  │  - Handles file uploads to /static/uploads/          │  │
│  │  - Routes to Unified Agent                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                      │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │     Unified Agent (unified_agent.py)               │  │
│  │  Single LangGraph Agent with these stages:         │  │
│  │                                                     │  │
│  │  1. WELCOME & INQUIRY                             │  │
│  │     - Greet user                                  │  │
│  │     - Ask loan amount & tenure                    │  │
│  │     - Extract loan_amount from message            │  │
│  │                                                     │  │
│  │  2. SALARY VERIFICATION                            │  │
│  │     - If payslip uploaded → Extract salary        │  │
│  │     - If salary typed → Ask for payslip           │  │
│  │     - Validate 2x rule (salary×24 ≥ 2×loan)      │  │
│  │                                                     │  │
│  │  3. KYC VERIFICATION                               │  │
│  │     - Request PAN number                          │  │
│  │     - Validate PAN format (ABCDE1000F)            │  │
│  │     - Call verification_agent_tool() to CRM       │  │
│  │                                                     │  │
│  │  4. UNDERWRITING                                   │  │
│  │     - Fetch credit score (Credit Bureau)          │  │
│  │     - Check pre-approved limit (Offer Mart)       │  │
│  │     - Calculate EMI                               │  │
│  │     - Evaluate: Approval/Rejection/Conditional    │  │
│  │                                                     │  │
│  │  5. SANCTION LETTER                                │  │
│  │     - If approved → Generate PDF                  │  │
│  │     - Return download link                        │  │
│  │                                                     │  │
│  │  State Management:                                 │  │
│  │  - messages[] : Conversation history              │  │
│  │  - customer_name, pan_number, phone               │  │
│  │  - loan_amount, monthly_salary                    │  │
│  │  - kyc_verified, credit_score                     │  │
│  │  - underwriting_status, sanction_letter_url       │  │
│  │                                                     │  │
│  │  Tools Available:                                  │  │
│  │  - verification_agent_tool() → CRM service        │  │
│  │  - underwriting_agent_tool() → Processing         │  │
│  │  - sanction_letter_tool() → PDF generation        │  │
│  │  - check_user_history_tool() → Database           │  │
│  │  - get_market_rates_tool() → Interest rates       │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                      │
│        ┌──────────────┼──────────────┬──────────────┐       │
│        ▼              ▼              ▼              ▼       │
└───────────────────────────────────────────────────────────────┘
        │              │              │              │
        │ File Upload  │ OCR          │ Tools        │ PDF
        │ Processing   │ Extraction   │ Calling      │ Generation
        ▼              ▼              ▼              ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │  Payslip │   │Tesseract │   │   Mock   │   │ReportLab │
  │ Storage  │   │  + PDF   │   │Services  │   │  Engine  │
  │          │   │Processing│   │  (5001)  │   │          │
  │/uploads/ │   │          │   │  (5002)  │   │/pdfs/    │
  │          │   │pytesseract   │  (5003)  │   │          │
  │          │   │pdfplumber    │          │   │          │
  │          │   │pdf2image     │          │   │          │
  └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

## Core Components

### 1. **Unified Agent** (`agents/unified_agent.py`)

**Responsibility**: Single intelligent agent that orchestrates the entire loan workflow

**Key Functions**:
- `agent_node(state)`: Main processing loop that receives user message + state, returns response
- `extract_loan_amount()`: Parses loan amount from text (handles lakh, thousand, rupees, numeric)
- `extract_salary()`: Parses monthly salary from text
- `extract_pan()`: Extracts and validates PAN number
- `validate_pan()`: Confirms PAN format (ABCDE1234F)

**State Management**:
```python
class AgentState(TypedDict):
    messages: list[AnyMessage]
    customer_name: Optional[str]
    pan_number: Optional[str]
    loan_amount: Optional[int]
    monthly_salary: Optional[int]
    kyc_verified: bool
    credit_score: Optional[int]
    underwriting_status: str
    sanction_letter_url: Optional[str]
```

**Prompt Engineering**:
- Explicit instructions to acknowledge salary uploads immediately
- Force re-extraction when payslip uploaded
- Ask for payslip if salary typed without upload
- Clear stage-by-stage workflow

### 2. **Flask API** (`app.py`)

**Endpoints**:
```
POST /chat
  Request: {message: string, session_id: string, file?: File}
  Response: {response: string}

GET / 
  Serves frontend index.html

GET /<static_file>
  Serves CSS, JS, PDFs, etc.

GET /health
  Returns {status: "ok"}
```

**File Upload Handling**:
```python
# Multipart/form-data processing
# 1. Receive file from FormData
# 2. Save to /static/uploads/ with session_id prefix
# 3. Process OCR if image/PDF
# 4. Extract salary from OCR
# 5. Create message: "I have uploaded my payslip. My monthly salary is..."
# 6. Send to unified agent
```

### 3. **OCR Pipeline** (`app.py`)

**Flow**:
```
Payslip Upload → File Type Check
                     ↓
              PDF? → pdf2image → Convert to images
                ↓
           pytesseract → Extract text
                ↓
           Regex parsing → Extract salary (₹45,000, etc.)
                ↓
           Create message → Send to agent
```

**Supported Formats**:
- PDF (text-based): pdfplumber
- PDF (image-based): pdf2image + pytesseract
- PNG/JPG: pytesseract

### 4. **Tools** (`agents/tools.py`)

**verification_agent_tool()**
```
Input: {pan: "ABCDE1000F"}
↓
Call: http://127.0.0.1:5001/verify-pan
↓
Output: {
  valid: true,
  customer_name: "Aarush Luthra",
  phone: "9876543210"
}
```

**underwriting_agent_tool()**
```
Input: {
  pan: "ABCDE1000F",
  loan_amount: 200000,
  monthly_salary: 70000,
  tenure: 24
}
↓
Logic:
- Fetch credit_score from Credit Bureau
- Fetch pre_approved_limit from Offer Mart
- Check: salary × 24 ≥ 2 × loan_amount
- Calculate EMI = loan_amount / 24
- Check: EMI ≤ 0.5 × monthly_salary
↓
Output: {
  status: "APPROVED" | "REJECTED" | "CONDITIONAL",
  reason: "...",
  max_loan_amount: 840000
}
```

**sanction_letter_tool()**
```
Input: Approved loan details
↓
ReportLab: Generate PDF with:
- Loan amount
- Interest rate
- Tenure
- EMI amount
- Customer details
↓
Save to: /static/pdfs/SESSIONID_sanction.pdf
↓
Return: Download URL
```

### 5. **Mock Services**

**CRM Service** (Port 5001)
```
POST /verify-pan
→ Check mock_bank.db
→ Return customer details or error
```

**Credit Bureau** (Port 5002)
```
POST /get-credit-score
→ Return random score (650-850)
```

**Offer Mart** (Port 5003)
```
POST /get-limit
→ Return pre-approved limit based on credit score
```

## Data Flow

### Happy Path (Approved Loan)

```
User: "I need ₹70,000 loan"
  ↓
Agent extracts: loan_amount = 70000
Agent response: "Got it! What's your monthly salary?"
  ↓
User: Uploads payslip.png
  ↓
Backend: OCR extracts ₹50,000 salary
Message created: "I have uploaded my payslip. My monthly salary is ₹50,000..."
  ↓
Agent receives message with salary
Agent response: "Thank you for uploading! Your salary is ₹50,000. 
                For a ₹70,000 loan, you qualify (2x rule met). 
                Now I need your PAN for KYC."
  ↓
User: "My PAN is ABCDE1000F"
  ↓
Agent calls verification_agent_tool()
  → CRM returns: "Valid, Aarush Luthra"
Agent response: "Thank you Aarush! Verifying your loan eligibility..."
  ↓
Agent calls underwriting_agent_tool()
  → Credit Bureau: 850 (excellent)
  → Offer Mart: ₹500,000 pre-approved limit
  → Check: 50000 × 24 = 1,200,000 ≥ 2 × 70,000 ✓
  → EMI = 2,917 ≤ 25,000 (50% of 50k) ✓
  → Result: APPROVED
  ↓
Agent calls sanction_letter_tool()
  → ReportLab generates PDF
  → Saves to /static/pdfs/demo_user_sanction.pdf
  ↓
Agent response: "Congratulations! Your loan of ₹70,000 is APPROVED!
                 EMI: ₹2,917/month for 24 months at 10% interest rate.
                 📄 Download your sanction letter: [LINK]"
```

### Salary Verification Path (Typed vs Upload)

```
User: "My monthly salary is ₹50,000"
  ↓
Agent detects: Salary typed, no payslip uploaded
  ↓
Agent response: "Thank you for sharing your salary. 
                However, to proceed, could you please upload your 
                payslip for verification?"
  ↓
User: Uploads payslip
  ↓
[Continues to underwriting as above]
```

## Key Design Decisions

1. **Single Agent vs Multi-Agent**
   - ✅ Simpler to debug and maintain
   - ✅ Single source of truth for state
   - ✅ Natural conversation flow
   - ❌ Less modular, harder to specialize agents

2. **Payslip OCR Requirement**
   - ✅ Secure salary verification
   - ✅ Prevents manual salary manipulation
   - ✅ Compliance-ready (KYC/AML)
   - ❌ Requires OCR accuracy

3. **Mock Services Instead of Real APIs**
   - ✅ Testing without external dependencies
   - ✅ Consistent test data
   - ✅ Fast development
   - ❌ Not production-ready

4. **Flask Frontend Serving**
   - ✅ Solves CORS issues
   - ✅ No need for separate frontend host
   - ✅ Single port deployment
   - ❌ Tightly couples frontend to backend

## Error Handling

**Graceful Degradation**:
```
Payslip OCR fails
  → Notify user: "Couldn't extract salary from image"
  → Ask user to type salary
  → Request payslip again later

CRM service down
  → Notify user: "Verification service temporarily unavailable"
  → Ask user to retry

Invalid PAN format
  → Notify user: "Please provide PAN in format ABCDE1234F"
  → Ask again
```

## Performance Considerations

- **Message Processing**: ~2-3 seconds (LLM latency dominant)
- **OCR Processing**: ~1-2 seconds for image payslips
- **PDF Generation**: <1 second
- **Database Queries**: <50ms (SQLite local)

## Security

- ✅ Input validation (PAN format, file types)
- ✅ File upload with secure_filename()
- ✅ Session-based conversation isolation
- ✅ No sensitive data in logs
- ✅ OCR doesn't store payslips (temp only)
- ❌ No encryption (dev-only, not production)

## Future Improvements

- Multi-language OCR support
- Real-time streaming responses
- WebSocket for persistent connections
- Redis for session management
- Kubernetes deployment
- Real bank API integration
- Document tampering detection
- Advanced fraud detection ML models
