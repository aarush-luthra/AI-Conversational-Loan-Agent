# app.py (improved)
import os
import json
import traceback
import re
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import ast
from agents.unified_agent import run_agent

# Configure Tesseract path (works on both Windows and Linux)
try:
    import pytesseract
    tesseract_path = os.getenv('TESSERACT_PATH', None)
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        print(f"✅ Tesseract-OCR configured from env: {tesseract_path}")
    elif os.name == 'nt':  # Windows
        default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(default_path):
            pytesseract.pytesseract.tesseract_cmd = default_path
            print("✅ Tesseract-OCR configured from default Windows path")
    else:
        print("✅ Tesseract-OCR will use system PATH (Linux/Docker)")
except ImportError:
    print("⚠️ pytesseract not installed")
except Exception as e:
    print(f"⚠️ Error configuring Tesseract: {e}")

# Configure Poppler path for pdf2image (optional, system PATH can be used)
POPPLER_PATH = os.getenv('POPPLER_PATH', None)
if POPPLER_PATH is None and os.name == 'nt':  # Windows
    default_poppler = r'C:\Users\Ritika\poppler\poppler-24.08.0\Library\bin'
    if os.path.exists(default_poppler):
        POPPLER_PATH = default_poppler
        print(f"✅ Poppler-utils configured from default Windows path")

# --- App setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "static", "pdfs")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_salary_from_file(filepath):
    """Extract salary information from uploaded payslip image/PDF using OCR"""
    try:
        text = ""
        
        # Handle PDF files
        if filepath.lower().endswith('.pdf'):
            try:
                import pdfplumber
                import pytesseract
                from PIL import Image
                import pdf2image
                
                print(f"📄 Processing PDF: {filepath}")
                
                # First try text extraction
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                
                print(f"📝 Extracted {len(text)} chars from PDF text layer")
                
                # If no text found, it's a scanned/image PDF - use OCR
                if len(text) < 50:
                    print("🔍 PDF appears to be image-based, using OCR...")
                    try:
                        # Convert PDF pages to images
                        images = pdf2image.convert_from_path(filepath, dpi=300, poppler_path=POPPLER_PATH)
                        print(f"📸 Converted PDF to {len(images)} image(s)")
                        
                        # OCR each page
                        for i, img in enumerate(images):
                            # Preprocess for better OCR
                            img = img.convert('L')  # Grayscale
                            page_text = pytesseract.image_to_string(img, config='--psm 6')
                            text += page_text
                            print(f"✅ OCR page {i+1}: {len(page_text)} chars")
                        
                        print(f"🎯 Total OCR extracted: {len(text)} chars")
                    except ImportError as ie:
                        print(f"❌ Missing package: {ie}")
                        print("Install: pip install pdf2image")
                        print("Also needs poppler: https://github.com/oschwartz10612/poppler-windows/releases/")
                        return None
                    except Exception as ocr_err:
                        print(f"❌ OCR error: {ocr_err}")
                        import traceback
                        traceback.print_exc()
                        return None
                        
            except Exception as pdf_error:
                print(f"❌ PDF extraction error: {pdf_error}")
                import traceback
                traceback.print_exc()
                return None
        
        # Handle image files (PNG, JPG, JPEG)
        elif filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                import pytesseract
                from PIL import Image
                
                print(f"🖼️ Processing image: {filepath}")
                
                # Open and preprocess image
                img = Image.open(filepath)
                img = img.convert('L')  # Grayscale
                
                # Extract text using OCR
                text = pytesseract.image_to_string(img, config='--psm 6')
                print(f"✅ OCR extracted {len(text)} chars from image")
                
            except ImportError as ie:
                print(f"❌ {ie} - pytesseract not installed")
                return None
            except Exception as ocr_error:
                print(f"❌ OCR error: {ocr_error}")
                import traceback
                traceback.print_exc()
                return None
        else:
            print(f"❌ Unsupported file type: {filepath}")
            return None
        
        if not text or len(text) < 10:
            print("No meaningful text extracted from file")
            return None
        
        # DEBUG: Print extracted text
        print(f"🔍 DEBUG - Extracted text:\n{text}\n")
        
        # Enhanced salary extraction patterns
        salary_patterns = [
            r'net\s*pay[:\s]*[₹rs.\s]*(\d+[,\d]*)',
            r'net\s*salary[:\s]*[₹rs.\s]*(\d+[,\d]*)',
            r'take\s*home[:\s]*[₹rs.\s]*(\d+[,\d]*)',
            r'monthly\s*salary[:\s]*[₹rs.\s]*(\d+[,\d]*)',
            r'basic\s*salary[:\s]*[₹rs.\s]*(\d+[,\d]*)',
            r'gross\s*salary[:\s]*[₹rs.\s]*(\d+[,\d]*)',
            r'₹\s*(\d{2}[,\d]+)',
            r'rs\.?\s*(\d{2}[,\d]+)',
        ]
        
        text_lower = text.lower()
        found_salaries = []
        
        for pattern in salary_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                salary_str = match.group(1).replace(',', '').replace(' ', '')
                try:
                    salary = int(salary_str)
                    if 10000 <= salary <= 500000:
                        found_salaries.append(salary)
                        print(f"Found potential salary: ₹{salary:,}")
                except ValueError:
                    continue
        
        if found_salaries:
            final_salary = max(found_salaries)
            print(f"Selected salary: ₹{final_salary:,}")
            return final_salary
        
        print("No salary found in document")
        return None
        
    except Exception as e:
        print(f"Error extracting salary from file: {e}")
        import traceback
        traceback.print_exc()
        return None

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"))
# Allow your frontend origin (adjust if needed). Using "*" is OK for local dev.
CORS(app, resources={r"/*": {"origins": "*"}})

# Serve frontend
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "..", "frontend")

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "pdf_dir": PDF_DIR})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        # Check if it's a file upload (multipart/form-data) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle file upload
            message = request.form.get("message", "Here is my payslip")
            session_id = request.form.get("session_id", "guest")
            
            uploaded_salary = None
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    try:
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(UPLOAD_DIR, f"{session_id}_{filename}")
                        file.save(filepath)
                        print(f"File saved: {filepath}")
                        
                        # Extract salary from file
                        extracted_salary = extract_salary_from_file(filepath)
                        if extracted_salary:
                            uploaded_salary = extracted_salary
                            # Make it clear to the agent that salary has been provided
                            message = f"I have uploaded my payslip. My monthly salary is ₹{extracted_salary:,}. Please verify my eligibility for the loan."
                            print(f"✅ Extracted salary: ₹{extracted_salary:,}")
                        else:
                            # If extraction fails, ask user to provide salary
                            message = f"I uploaded a payslip file ({filename}), but the salary could not be extracted automatically. Can you help me verify my eligibility? (You may need to ask me for my salary)"
                            print("⚠️ Could not extract salary from file")
                    except Exception as file_error:
                        print(f"Error processing file: {file_error}")
                        import traceback
                        traceback.print_exc()
                        message = f"{message}. I tried to upload a payslip but you can ask me to type my salary instead."
        else:
            # Handle JSON request
            data = request.get_json(force=True, silent=True) or {}
            message = data.get("message", "")
            session_id = data.get("session_id", "guest")

        # run the unified agent workflow
        raw_response = run_agent(message, session_id)

        # Normalize response types:
        cleaned_response = None

        # If run_agent returned a dict/list (structured state), try to extract final text
        if isinstance(raw_response, dict):
            # try common keys
            for key in ("final_response", "response", "text"):
                if key in raw_response:
                    cleaned_response = raw_response[key]
                    break
            if cleaned_response is None:
                # fallback: stringify meaningful parts
                cleaned_response = json.dumps(raw_response)
        elif isinstance(raw_response, list):
            cleaned_response = " ".join([str(x) for x in raw_response])
        elif isinstance(raw_response, str):
            stripped = raw_response.strip()
            # If Gemini returns a stringified dict like "{'type': 'text', 'text': 'hi'}"
            if stripped.startswith("{") and "'type': 'text'" in stripped:
                try:
                    parsed = ast.literal_eval(stripped)
                    cleaned_response = parsed.get("text", raw_response)
                except Exception:
                    cleaned_response = raw_response
            else:
                cleaned_response = raw_response
        else:
            cleaned_response = str(raw_response)

        return jsonify({"response": cleaned_response})

    except Exception as e:
        # Print stacktrace to terminal for debugging
        tb = traceback.format_exc()
        print("ERROR in /chat:", tb)
        return jsonify({"response": f"System Error: {str(e)}", "trace": tb}), 500


@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    """Streaming endpoint using Server-Sent Events (SSE).
    
    This endpoint streams responses in real-time as they are generated,
    providing a more responsive user experience.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        message = data.get("message", "")
        session_id = data.get("session_id", "guest")
        
        def generate():
            """Generator function for SSE streaming."""
            try:
                for chunk in run_agent_stream(message, session_id):
                    if chunk:
                        # Format as SSE data event
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Send done signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR in /chat/stream:", tb)
        return jsonify({"error": f"System Error: {str(e)}", "trace": tb}), 500


@app.route("/static/pdfs/<path:filename>")
def serve_pdf(filename):
    # Safe serving from absolute PDF_DIR
    return send_from_directory(PDF_DIR, filename, as_attachment=False)


if __name__ == "__main__":
    # Production: Use PORT env var (Render sets this)
    # Development: Default to 5000
    port = int(os.getenv('PORT', 5000))
    is_production = os.getenv('FLASK_ENV', 'development') == 'production'
    
    # In production, listen on all interfaces (0.0.0.0)
    # In development, listen only on localhost (127.0.0.1)
    host = '0.0.0.0' if is_production else '127.0.0.1'
    
    print(f"Starting backend on {host}:{port} (Flask Environment: {'production' if is_production else 'development'})")
    app.run(host=host, port=port, debug=not is_production)

