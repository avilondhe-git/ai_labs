import azure.functions as func
import azure.durable_functions as df
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from src.utils.config import settings
from src.models.document import InvoiceData
import logging


@df.DFApp.activity_trigger(input_name="blob_name")
def process_invoice(blob_name: str) -> dict:
    """Process invoice using Azure Document Intelligence prebuilt model"""
    logging.info(f"Processing invoice: {blob_name}")
    
    blob_client = BlobServiceClient.from_connection_string(
        settings.AZURE_STORAGE_CONNECTION_STRING
    ).get_blob_client("documents", blob_name)
    blob_url = blob_client.url
    
    if settings.DOCUMENT_INTELLIGENCE_KEY:
        credential = AzureKeyCredential(settings.DOCUMENT_INTELLIGENCE_KEY)
    else:
        credential = DefaultAzureCredential()
    
    doc_client = DocumentAnalysisClient(
        endpoint=settings.DOCUMENT_INTELLIGENCE_ENDPOINT,
        credential=credential
    )
    
    poller = doc_client.begin_analyze_document_from_url(
        "prebuilt-invoice",
        blob_url
    )
    result = poller.result()
    
    invoice_data = InvoiceData()
    
    if result.documents:
        invoice = result.documents[0]
        fields = invoice.fields
        
        invoice_data.vendor_name = fields.get("VendorName", {}).get("content")
        invoice_data.invoice_number = fields.get("InvoiceId", {}).get("content")
        invoice_data.invoice_date = fields.get("InvoiceDate", {}).get("content")
        invoice_data.due_date = fields.get("DueDate", {}).get("content")
        invoice_data.subtotal = fields.get("SubTotal", {}).get("content")
        invoice_data.tax = fields.get("TotalTax", {}).get("content")
        invoice_data.total = fields.get("InvoiceTotal", {}).get("content")
        
        items_field = fields.get("Items")
        if items_field:
            for item in items_field.value:
                item_fields = item.value
                invoice_data.line_items.append({
                    "description": item_fields.get("Description", {}).get("content"),
                    "quantity": item_fields.get("Quantity", {}).get("content"),
                    "unit_price": item_fields.get("UnitPrice", {}).get("content"),
                    "amount": item_fields.get("Amount", {}).get("content")
                })
        
        calculated_total = sum(
            float(item.get("amount", 0) or 0) for item in invoice_data.line_items
        )
        expected_total = float(invoice_data.total or 0)
        
        if abs(calculated_total - expected_total) < 0.01:
            invoice_data.math_valid = True
        else:
            invoice_data.math_valid = False
            invoice_data.anomalies.append(
                f"Line items total ({calculated_total}) doesn't match invoice total ({expected_total})"
            )
    
    return {
        "document_id": blob_name,
        "document_type": "invoice",
        "extracted_data": invoice_data.model_dump(),
        "raw_text": result.content,
        "needs_review": not invoice_data.math_valid
    }
