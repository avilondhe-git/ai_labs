import azure.functions as func
import azure.durable_functions as df
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from src.utils.config import settings
from src.utils.monitoring import log_metric, log_event
import logging

app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.blob_trigger(arg_name="blob", path="documents/{name}",
                  connection="AZURE_STORAGE_CONNECTION_STRING")
async def document_uploaded(blob: func.InputStream):
    """Triggered when document uploaded to Blob Storage"""
    logging.info(f"Document uploaded: {blob.name}")
    
    client = df.DurableOrchestrationClient()
    instance_id = await client.start_new(
        "process_document_orchestrator",
        None,
        {
            "blob_name": blob.name,
            "blob_size": blob.length,
            "content_type": blob.content_type
        }
    )
    
    log_event("document_uploaded", {
        "blob_name": blob.name,
        "instance_id": instance_id
    })


@app.orchestration_trigger(context_name="context")
def process_document_orchestrator(context: df.DurableOrchestrationContext):
    """Main orchestration workflow for document processing"""
    input_data = context.get_input()
    blob_name = input_data["blob_name"]
    
    document_type = yield context.call_activity(
        "classify_document",
        blob_name
    )
    
    processor_map = {
        "invoice": "process_invoice",
        "contract": "process_contract",
        "generic": "process_generic_document"
    }
    
    processor = processor_map.get(document_type, "process_generic_document")
    extracted_data = yield context.call_activity(processor, blob_name)
    
    enriched_data = yield context.call_activity(
        "enrich_with_ai",
        extracted_data
    )
    
    yield context.call_activity("store_metadata", enriched_data)
    
    yield context.call_activity("index_document", enriched_data)
    
    if enriched_data.get("needs_review"):
        yield context.call_activity("send_for_review", enriched_data)
    
    return {"status": "completed", "document_id": enriched_data["document_id"]}


@app.activity_trigger(input_name="blob_name")
def classify_document(blob_name: str) -> str:
    """Classify document type using Azure OpenAI"""
    from openai import AzureOpenAI
    from azure.storage.blob import BlobServiceClient
    
    blob_client = BlobServiceClient.from_connection_string(
        settings.AZURE_STORAGE_CONNECTION_STRING
    ).get_blob_client("documents", blob_name)
    
    content = blob_client.download_blob().readall().decode('utf-8', errors='ignore')[:1000]
    
    client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION
    )
    
    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "Classify this document type. Respond with ONLY one word: invoice, contract, receipt, form, research_paper, or generic."},
            {"role": "user", "content": f"Document content:\n{content}"}
        ],
        temperature=0
    )
    
    doc_type = response.choices[0].message.content.strip().lower()
    logging.info(f"Classified {blob_name} as {doc_type}")
    
    return doc_type
