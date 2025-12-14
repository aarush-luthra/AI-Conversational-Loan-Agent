from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, grey
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime, timedelta
import uuid
from pathlib import Path

class PDFService:
    def __init__(self, output_dir=None):
        # Use absolute path to ensure PDFs are saved in the correct location
        if output_dir is None:
            # Get the directory where this file is located
            current_dir = Path(__file__).parent.parent
            output_dir = current_dir / "static" / "pdfs"
        
        self.output_dir = str(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Company branding colors
        self.primary_color = HexColor('#1a237e')  # Deep blue
        self.secondary_color = HexColor('#0d47a1')  # Medium blue
        self.accent_color = HexColor('#2196f3')  # Light blue
        self.text_color = black
        self.grey_color = grey
    
    def _calculate_emi(self, principal, annual_rate, tenure_months):
        """Calculate monthly EMI using reducing balance method"""
        monthly_rate = annual_rate / (12 * 100)
        if monthly_rate == 0:
            return principal / tenure_months
        
        emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / \
              (((1 + monthly_rate) ** tenure_months) - 1)
        return round(emi, 2)
    
    def _format_currency(self, amount):
        """Format amount in Indian currency format"""
        s = str(int(amount))
        if len(s) <= 3:
            return f"₹{s}"
        
        # Indian numbering: last 3 digits, then groups of 2
        last_three = s[-3:]
        remaining = s[:-3]
        
        if remaining:
            groups = []
            while remaining:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
            formatted = ','.join(reversed(groups)) + ',' + last_three
        else:
            formatted = last_three
        
        return f"₹{formatted}"
    
    def generate(self, name, amount, interest, pan=None, tenure=24, processing_fee=1.5):
        """Generate professional sanction letter PDF with complete loan details
        
        Args:
            name: Customer name
            amount: Loan amount
            interest: Annual interest rate (%)
            pan: PAN number (optional)
            tenure: Loan tenure in months (default: 24)
            processing_fee: Processing fee percentage (default: 1.5%)
        
        Returns:
            str: Generated PDF filename
        """
        filename = f"Sanction_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create canvas
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Generate unique loan ID
        loan_id = f"NXS{datetime.now().strftime('%Y%m')}{str(uuid.uuid4().hex[:6].upper())}"
        
        # Calculate loan details
        emi = self._calculate_emi(amount, interest, tenure)
        processing_fee_amount = amount * (processing_fee / 100)
        total_repayment = emi * tenure
        total_interest = total_repayment - amount
        
        # === HEADER SECTION ===
        y = height - 50
        
        # Company name and logo area
        c.setFillColor(self.primary_color)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, y, "NEXUS FINANCE")
        
        c.setFont("Helvetica", 10)
        c.setFillColor(self.grey_color)
        c.drawString(50, y - 15, "Your Trusted Financial Partner")
        
        # Date and Loan ID on right
        c.setFont("Helvetica", 9)
        c.drawRightString(width - 50, y, f"Date: {datetime.now().strftime('%d %B %Y')}")
        c.drawRightString(width - 50, y - 15, f"Loan ID: {loan_id}")
        
        # Horizontal line
        y -= 35
        c.setStrokeColor(self.accent_color)
        c.setLineWidth(2)
        c.line(50, y, width - 50, y)
        
        # === TITLE ===
        y -= 40
        c.setFillColor(self.primary_color)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, y, "LOAN SANCTION LETTER")
        
        # === CUSTOMER DETAILS ===
        y -= 50
        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Customer Details:")
        
        y -= 20
        c.setFont("Helvetica", 11)
        c.drawString(70, y, f"Name: {name}")
        
        if pan:
            y -= 18
            c.drawString(70, y, f"PAN: {pan}")
        
        # === LOAN DETAILS BOX ===
        y -= 40
        c.setFillColor(self.primary_color)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Loan Details:")
        
        # Draw box
        y -= 25
        box_height = 140
        c.setStrokeColor(self.accent_color)
        c.setLineWidth(1)
        c.roundRect(50, y - box_height, width - 100, box_height, 5)
        
        # Loan details content
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 10)
        
        details = [
            ("Sanctioned Amount:", self._format_currency(amount)),
            ("Interest Rate:", f"{interest}% per annum"),
            ("Loan Tenure:", f"{tenure} months"),
            ("Processing Fee:", f"{self._format_currency(processing_fee_amount)} ({processing_fee}%)"),
            ("Monthly EMI:", self._format_currency(emi)),
            ("Total Interest:", self._format_currency(total_interest)),
            ("Total Repayment:", self._format_currency(total_repayment)),
        ]
        
        y_detail = y - 20
        for label, value in details:
            c.setFont("Helvetica", 10)
            c.drawString(70, y_detail, label)
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(width - 70, y_detail, value)
            y_detail -= 18
        
        # === REPAYMENT SCHEDULE ===
        y = y - box_height - 40
        c.setFillColor(self.primary_color)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Repayment Schedule:")
        
        y -= 20
        c.setFont("Helvetica", 9)
        c.setFillColor(self.text_color)
        
        # Table header
        c.setFont("Helvetica-Bold", 9)
        c.drawString(60, y, "Month")
        c.drawString(150, y, "EMI Amount")
        c.drawString(250, y, "Principal")
        c.drawString(350, y, "Interest")
        c.drawString(450, y, "Balance")
        
        # Draw header line
        y -= 5
        c.setStrokeColor(self.grey_color)
        c.line(50, y, width - 50, y)
        
        # Sample schedule (first 3 months and last month)
        y -= 15
        c.setFont("Helvetica", 8)
        
        balance = amount
        monthly_rate = interest / (12 * 100)
        
        for month in [1, 2, 3]:
            interest_component = balance * monthly_rate
            principal_component = emi - interest_component
            balance -= principal_component
            
            c.drawString(60, y, str(month))
            c.drawString(150, y, self._format_currency(emi))
            c.drawString(250, y, self._format_currency(principal_component))
            c.drawString(350, y, self._format_currency(interest_component))
            c.drawString(450, y, self._format_currency(balance))
            y -= 12
        
        # Ellipsis
        c.drawString(60, y, "...")
        y -= 12
        
        # Last month
        c.drawString(60, y, str(tenure))
        c.drawString(150, y, self._format_currency(emi))
        c.drawString(450, y, self._format_currency(0))
        
        # === TERMS AND CONDITIONS ===
        y -= 30
        c.setFillColor(self.primary_color)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Terms and Conditions:")
        
        y -= 18
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 8)
        
        terms = [
            "1. This sanction is valid for 30 days from the date of issue.",
            "2. Disbursement is subject to verification of documents and credit assessment.",
            "3. EMI payments must be made on or before the due date each month.",
            "4. Late payment charges of 2% per month will apply on overdue amounts.",
            "5. Prepayment is allowed with a foreclosure charge of 4% on outstanding principal.",
            "6. The loan is subject to the terms and conditions mentioned in the loan agreement.",
        ]
        
        for term in terms:
            c.drawString(60, y, term)
            y -= 12
        
        # === FOOTER ===
        y -= 30
        c.setStrokeColor(self.accent_color)
        c.setLineWidth(1)
        c.line(50, y, width - 50, y)
        
        y -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y, "Authorized Signatory")
        
        y -= 25
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(self.grey_color)
        c.drawString(50, y, "This is a computer-generated document and does not require a physical signature.")
        
        # Company footer
        y = 50
        c.setFont("Helvetica", 7)
        c.setFillColor(self.grey_color)
        footer_text = "Nexus Finance Ltd. | CIN: U65999MH2024PLC123456 | Registered Office: Mumbai, India"
        c.drawCentredString(width / 2, y, footer_text)
        c.drawCentredString(width / 2, y - 10, "Email: support@nexusfinance.com | Phone: 1800-123-4567 | Website: www.nexusfinance.com")
        
        # Save PDF
        c.save()
        return filename