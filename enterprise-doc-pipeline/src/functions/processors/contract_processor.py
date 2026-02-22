import azure.functions as func
import azure.durable_functions as df
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI
from src.utils.config import settings
from src.models.document import ContractData
import logging
import json


@df.DFApp.activity_trigger(input_name="blob_name")
def process_contract(blob_name: str) -> dict:
    """Process contract using Azure Document Intelligence + GPT-4o extraction"""
    logging.info(f"Processing contract: {blob_name}")
    
    blob_client = BlobServiceClient.from_connection_string(
        settings.AZURE_STORAGE_CONNECTION_STRING
    ).get_blob_client("documents", blob_name)
    blob_url = blob_client.url
    
    credential = AzureKeyCredential(settings.DOCUMENT_INTELLIGENCE_KEY)
    doc_client = DocumentAnalysisClient(
        endpoint=settings.DOCUMENT_INTELLIGENCE_ENDPOINT,
        credential=credential
    )
    
    poller = doc_client.begin_analyze_document_from_url("prebuilt-layout", blob_url)
    result = poller.result()
    
    full_text = result.content
    
    openai_client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION
    )
    
    extraction_prompt = """
Extract the following information from this contract:
1. Parties involved (list of company/person names)
2. Effective date
3. Expiration date
4. Auto-renewal clause (yes/no)
5. Payment terms
6. Termination clause
7. Liability cap amount
8. Key obligations (list)
9. Deliverables (list)
10. Risk flags (e.g., "unlimited liability", "perpetual contract", "auto-renewal")

Return as JSON with these exact keys: parties, effective_date, expiration_date, auto_renewal, payment_terms, termination_clause, liability_cap, obligations, deliverables, risk_flags
"""
    
    response = openai_client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": extraction_prompt},
            {"role": "user", "content": f"Contract text:\n\n{full_text[:8000]}"}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    extracted_json = json.loads(response.choices[0].message.content)
    contract_data = ContractData(**extracted_json)
    
    needs_review = len(contract_data.risk_flags) > 0
    
    return {
        "document_id": blob_name,
        "document_type": "contract",
        "extracted_data": contract_data.model_dump(),
        "raw_text": full_text,
        "needs_review": needs_review
    }
