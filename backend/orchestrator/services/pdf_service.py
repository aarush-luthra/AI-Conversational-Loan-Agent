from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

class PDFService:
    def __init__(self, output_dir="orchestrator/static/pdfs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, name, amount, interest):
        filename = f"Sanction_{name.replace(' ', '_')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        c = canvas.Canvas(filepath, pagesize=letter)
        c.drawString(100, 700, "NBFC LOAN SANCTION LETTER")
        c.drawString(100, 680, f"Customer: {name}")
        c.drawString(100, 660, f"Approved Amount: INR {amount}")
        c.drawString(100, 640, f"Interest Rate: {interest}%")
        c.drawString(100, 600, "Approved by Team Nexus AI")
        c.save()
        return filename