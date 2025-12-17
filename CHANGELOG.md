# Changelog

All notable changes to this project are documented here.

## [Latest] - December 17, 2025

### Major Changes

#### Architecture Refactoring
- **Moved from Multi-Agent to Unified Single-Agent**: Simplified from supervisor-worker pattern to single intelligent agent handling entire workflow
- **Agent Framework**: LangGraph unified agent architecture (simplified from multi-agent approach)
- **LLM Migration**: Changed from Groq (Llama 3.1) to OpenAI GPT-4o-mini for better conversational quality

#### New OCR & Payslip Features
- **Payslip Upload Support**: Users can upload PDF/PNG/JPG payslips directly in chat
- **Automatic Salary Extraction**: Tesseract-OCR extracts monthly salary from payslips automatically
- **Payslip Confirmation Logic**: If user types salary without uploading, agent asks for payslip verification
- **Multi-format PDF Support**: Handles both text-based and image-based PDFs using pdfplumber + pdf2image
- **OCR Integration**: Installed and configured Tesseract-OCR with Python wrapper (pytesseract)

#### Frontend Improvements
- **Message Layout Fix**: Messages now stack vertically (user right, bot left) instead of horizontally
- **Button Type Fix**: Changed default buttons to `type="button"` to prevent unintended form submission
- **Page Reload Prevention**: Added `preventDefault()` on Enter key and form submission
- **Flask Frontend Serving**: Backend now serves frontend from Flask at `http://127.0.0.1:5000` instead of file:// protocol
- **Responsive Styling**: Improved CSS with proper flex layout and message bubble sizing

#### Salary & Eligibility Validation
- **2x Salary Rule**: Validates loan_amount ≤ 2 × (monthly_salary × 24)
- **EMI Validation**: Ensures estimated_emi ≤ 50% of monthly_salary
- **Smart Salary Detection**: Only accepts salary from payslip uploads, asks for confirmation if typed
- **Dynamic Eligibility Response**: Shows detailed breakdown of loan eligibility with calculations

#### Database & Mock Services
- **SQLite Mock Database**: Created `mock_bank.db` with 1005 test customers
- **Test PAN Range**: ABCDE1000F through ABCDE5000F with varying credit scores
- **Mock Service Fixes**: Added proper error handling and database path configuration

#### API & Integration
- **CORS Configuration**: Enabled CORS for all endpoints
- **File Upload Support**: Implemented multipart/form-data handling in Flask
- **Session Management**: Session-based conversation tracking with demo_user
- **Secure File Handling**: Uses werkzeug.utils.secure_filename for uploaded files

### Fixed Issues

- ✅ Fixed blank screen after payslip upload (button type issue)
- ✅ Fixed messages disappearing after form submission (preventDefault)
- ✅ Fixed CORS errors when frontend served as file://
- ✅ Fixed OCR not extracting salary from image-based PDFs (added pdf2image)
- ✅ Fixed mock services not responding (created database, fixed paths)
- ✅ Fixed loan amount extraction from salary (separate regex parsing)
- ✅ Fixed KeyError in prompt formatting (proper variable initialization)
- ✅ Fixed horizontal message layout (CSS flex-direction fix)
- ✅ Fixed message content not displaying (proper DOM structure with bubble div)

### Dependencies Changed

**Added:**
- `langchain-openai==0.1.1` - OpenAI integration
- `pytesseract==0.3.10` - Tesseract OCR wrapper
- `pdf2image==1.17.0` - PDF to image conversion
- `pdfplumber==0.10.4` - PDF text extraction
- `marked==0.3.0` - Markdown rendering

**Removed:**
- `langchain-groq` - Replaced with OpenAI
- `google-genai` - No longer needed
- `Flask-CKEditor`, `Flask-Gravatar`, `Flask-Login`, `Flask-SQLAlchemy`, `Flask-WTF` - Unused
- `Bootstrap-Flask`, `colorgram.py`, `faker`, `honcho` - Not required

**Updated:**
- `Flask==2.3.3` - Stable version
- `langchain==1.1.3` - Latest compatible version
- `langgraph==1.0.4` - Latest version

### Configuration

**Environment Variables:**
```bash
OPENAI_API_KEY="sk-proj-..." # OpenAI API key required
```

**Tesseract-OCR Setup:**
- Windows: Must install separately (see INSTALL_TESSERACT.md)
- Expected path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**Poppler for PDF Processing:**
- Required for pdf2image
- Download from: https://github.com/oschwartz10612/poppler-windows/releases/
- Expected path: `C:\Users\[USERNAME]\poppler\poppler-24.08.0\Library\bin`

### Testing

**Sample Test Flow:**
1. Say: "I need a loan for ₹70,000"
2. Upload: sample_payslip.png (located in frontend folder)
3. Provide: PAN number ABCDE1000F
4. Result: System verifies and approves/rejects with explanation

**Test PANs:**
- ABCDE1000F - Approved (₹500,000 limit, 850 credit score)
- ABCDE2000F - Rejected (low credit score)
- ABCDE3000F - Conditional (requires higher salary)

### Breaking Changes

- Unified agent replaces multi-agent workflow - simpler but less modular
- OpenAI API key required (Groq no longer used)
- Tesseract-OCR must be manually installed on Windows
- Frontend must be served via Flask (no more file:// protocol)

### Known Limitations

- Salary can only be confirmed via payslip upload (security/verification)
- Mock services must run on specific ports (5001-5003)
- Tesseract-OCR accuracy depends on payslip quality
- Image-based PDFs may have extraction errors for poor scans

### Future Improvements

- [ ] Support for multiple document types (salary certificates, bank statements)
- [ ] Real-time credit score integration
- [ ] Multi-language support for payslip OCR
- [ ] Blockchain for audit trail
- [ ] Advanced fraud detection
- [ ] Real NBFC integration

### Contributors

Team Nexus - EY Techathon 6.0 (BFSI Track)
