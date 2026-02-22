import pytest
from src.functions.processors.invoice_processor import process_invoice
from src.functions.processors.contract_processor import process_contract
import os


@pytest.fixture
def sample_invoice_blob():
    return "sample-documents/invoice.pdf"


@pytest.fixture
def sample_contract_blob():
    return "sample-documents/contract.pdf"


def test_invoice_processing(sample_invoice_blob):
    """Test invoice extraction"""
    result = process_invoice(sample_invoice_blob)
    
    assert result["document_type"] == "invoice"
    assert "extracted_data" in result
    assert "vendor_name" in result["extracted_data"]
    assert "invoice_number" in result["extracted_data"]


def test_contract_processing(sample_contract_blob):
    """Test contract extraction"""
    result = process_contract(sample_contract_blob)
    
    assert result["document_type"] == "contract"
    assert "extracted_data" in result
    assert "parties" in result["extracted_data"]


def test_math_validation():
    """Test invoice math validation"""
    from src.models.document import InvoiceData
    
    invoice = InvoiceData(
        line_items=[
            {"amount": 100.0},
            {"amount": 50.0}
        ],
        total=150.0
    )
    
    calculated = sum(item["amount"] for item in invoice.line_items)
    assert abs(calculated - invoice.total) < 0.01
