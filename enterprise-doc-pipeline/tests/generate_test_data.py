"""
Generate Test Documents for Enterprise Document Pipeline
Purpose: Create sample PDFs for testing invoice, contract, and form processing
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from pathlib import Path
from datetime import datetime, timedelta


def create_invoice_pdf(filename: str):
    """Create a sample invoice PDF"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("INVOICE", styles['Title']))
    story.append(Spacer(1, 12))
    
    vendor_info = [
        "Acme Corporation",
        "123 Business Street",
        "New York, NY 10001",
        "Phone: (555) 123-4567"
    ]
    for line in vendor_info:
        story.append(Paragraph(line, styles['Normal']))
    
    story.append(Spacer(1, 24))
    
    invoice_date = datetime.now()
    due_date = invoice_date + timedelta(days=30)
    
    invoice_details = [
        f"Invoice Number: INV-2024-001",
        f"Invoice Date: {invoice_date.strftime('%Y-%m-%d')}",
        f"Due Date: {due_date.strftime('%Y-%m-%d')}",
        f"Customer: XYZ Enterprises"
    ]
    for line in invoice_details:
        story.append(Paragraph(line, styles['Normal']))
    
    story.append(Spacer(1, 24))
    
    data = [
        ['Description', 'Quantity', 'Unit Price', 'Amount'],
        ['Software License', '5', '$200.00', '$1,000.00'],
        ['Professional Services', '20', '$150.00', '$3,000.00'],
        ['Support Package', '1', '$500.00', '$500.00'],
    ]
    
    table = Table(data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    
    story.append(Spacer(1, 24))
    
    totals = [
        "Subtotal: $4,500.00",
        "Tax (8%): $360.00",
        "Total Due: $4,860.00"
    ]
    for line in totals:
        story.append(Paragraph(f"<b>{line}</b>", styles['Normal']))
    
    story.append(Spacer(1, 24))
    story.append(Paragraph("Payment Terms: Net 30 days", styles['Normal']))
    story.append(Paragraph("Thank you for your business!", styles['Normal']))
    
    doc.build(story)


def create_contract_pdf(filename: str):
    """Create a sample contract PDF"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("SERVICE AGREEMENT", styles['Title']))
    story.append(Spacer(1, 24))
    
    effective_date = datetime.now()
    expiration_date = effective_date + timedelta(days=365)
    
    story.append(Paragraph(f"<b>Effective Date:</b> {effective_date.strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Paragraph(f"<b>Expiration Date:</b> {expiration_date.strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>PARTIES:</b>", styles['Heading2']))
    story.append(Paragraph("This agreement is entered into between:", styles['Normal']))
    story.append(Paragraph("1. <b>Acme Corporation</b> (the 'Service Provider')", styles['Normal']))
    story.append(Paragraph("2. <b>XYZ Enterprises Inc.</b> (the 'Client')", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>SERVICES:</b>", styles['Heading2']))
    services = [
        "Software development and maintenance services",
        "Technical support and consultation",
        "Cloud infrastructure management",
        "Security monitoring and updates"
    ]
    for service in services:
        story.append(Paragraph(f"• {service}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>PAYMENT TERMS:</b>", styles['Heading2']))
    story.append(Paragraph("The Client agrees to pay $10,000 per month for services rendered. Payment is due within 15 days of invoice date. Late payments will incur a 1.5% monthly interest charge.", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>OBLIGATIONS:</b>", styles['Heading2']))
    obligations = [
        "Service Provider shall deliver services in a timely and professional manner",
        "Client shall provide necessary access and information for service delivery",
        "Both parties shall maintain confidentiality of proprietary information",
        "Service Provider shall maintain appropriate insurance coverage"
    ]
    for obligation in obligations:
        story.append(Paragraph(f"• {obligation}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>TERMINATION:</b>", styles['Heading2']))
    story.append(Paragraph("Either party may terminate this agreement with 30 days written notice. Upon termination, Client shall pay for all services rendered up to the termination date.", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>LIABILITY:</b>", styles['Heading2']))
    story.append(Paragraph("Service Provider's total liability under this agreement shall not exceed $50,000 or the total fees paid in the preceding 12 months, whichever is greater.", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>AUTO-RENEWAL:</b>", styles['Heading2']))
    story.append(Paragraph("This agreement will automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least 60 days prior to the expiration date.", styles['Normal']))
    
    doc.build(story)


def create_form_pdf(filename: str):
    """Create a sample form PDF"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("INSURANCE CLAIM FORM", styles['Title']))
    story.append(Spacer(1, 24))
    
    story.append(Paragraph("<b>CLAIMANT INFORMATION</b>", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    fields = [
        "Full Name: John Smith",
        "Policy Number: POL-12345-6789",
        "Date of Birth: 01/15/1980",
        "Contact Number: (555) 987-6543",
        "Email: john.smith@example.com",
        "Address: 456 Main Street, Los Angeles, CA 90001"
    ]
    for field in fields:
        story.append(Paragraph(field, styles['Normal']))
        story.append(Spacer(1, 6))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>INCIDENT INFORMATION</b>", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    incident_info = [
        f"Date of Incident: {datetime.now().strftime('%m/%d/%Y')}",
        "Type of Claim: Auto Accident",
        "Location: Highway 101 at Main Street Exit",
        "Description: Vehicle collision with another car at intersection. Driver-side damage to front bumper and fender."
    ]
    for info in incident_info:
        story.append(Paragraph(info, styles['Normal']))
        story.append(Spacer(1, 6))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>CLAIM AMOUNT</b>", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    claim_details = [
        "Estimated Repair Cost: $3,500.00",
        "Deductible: $500.00",
        "Claim Amount: $3,000.00"
    ]
    for detail in claim_details:
        story.append(Paragraph(f"<b>{detail}</b>", styles['Normal']))
        story.append(Spacer(1, 6))
    
    story.append(Spacer(1, 24))
    story.append(Paragraph("I certify that the information provided is true and accurate to the best of my knowledge.", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%m/%d/%Y')}", styles['Normal']))
    
    doc.build(story)


def create_receipt_pdf(filename: str):
    """Create a sample receipt PDF"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph("RECEIPT", styles['Title']))
    story.append(Spacer(1, 24))
    
    store_info = [
        "Best Buy Electronics",
        "789 Shopping Plaza",
        "San Francisco, CA 94102",
        "Phone: (555) 246-8135"
    ]
    for line in store_info:
        story.append(Paragraph(line, styles['Normal']))
    
    story.append(Spacer(1, 24))
    
    receipt_details = [
        f"Receipt Number: REC-{datetime.now().strftime('%Y%m%d')}-001",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "Cashier: Employee #4523"
    ]
    for detail in receipt_details:
        story.append(Paragraph(detail, styles['Normal']))
    
    story.append(Spacer(1, 24))
    
    data = [
        ['Item', 'Quantity', 'Price'],
        ['Laptop Computer', '1', '$899.99'],
        ['Wireless Mouse', '1', '$29.99'],
        ['USB Cable', '2', '$19.98'],
    ]
    
    table = Table(data, colWidths=[4*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    
    story.append(Spacer(1, 24))
    
    totals = [
        "Subtotal: $949.96",
        "Tax (8.5%): $80.75",
        "Total: $1,030.71"
    ]
    for line in totals:
        story.append(Paragraph(f"<b>{line}</b>", styles['Normal']))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("Payment Method: Credit Card ****1234", styles['Normal']))
    story.append(Spacer(1, 24))
    story.append(Paragraph("Thank you for your purchase!", styles['Normal']))
    
    doc.build(story)


def generate_all_test_documents():
    """Generate a complete set of test documents"""
    output_dir = Path("sample-documents")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    create_invoice_pdf(str(output_dir / "invoice.pdf"))
    print("  - invoice.pdf")
    
    create_contract_pdf(str(output_dir / "contract.pdf"))
    print("  - contract.pdf")
    
    create_form_pdf(str(output_dir / "insurance_claim.pdf"))
    print("  - insurance_claim.pdf")
    
    create_receipt_pdf(str(output_dir / "receipt.pdf"))
    print("  - receipt.pdf")
    
    print(f"\nGenerated 4 test PDF documents in {output_dir}")


if __name__ == "__main__":
    print("\nGenerating Test Documents for Enterprise Document Pipeline...")
    print()
    generate_all_test_documents()
    print("\nTest documents ready for processing!")
