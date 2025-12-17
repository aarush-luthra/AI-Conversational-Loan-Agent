# Installing Tesseract-OCR for Payslip Image Reading

## Windows Installation

1. Download Tesseract-OCR installer:
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download: `tesseract-ocr-w64-setup-5.3.3.20231005.exe` (or latest version)

2. Run the installer:
   - Default installation path: `C:\Program Files\Tesseract-OCR`
   - Make sure to check "Add to PATH" during installation

3. Verify installation:
   ```powershell
   tesseract --version
   ```

4. If not in PATH, add manually:
   - Open System Environment Variables
   - Add to PATH: `C:\Program Files\Tesseract-OCR`
   - Restart your terminal

## Alternative: Use PDF Payslips

If you can't install Tesseract-OCR, you can:
1. Upload PDF payslips instead of images (works without OCR)
2. Simply type your salary in the chat (e.g., "My monthly salary is 45000")

## Testing

Once installed, test the upload feature:
1. Start the backend: `python backend\orchestrator\app.py`
2. Open frontend in browser
3. Click the paperclip icon (📎)
4. Upload a payslip image or PDF
5. The system will extract your salary automatically!
