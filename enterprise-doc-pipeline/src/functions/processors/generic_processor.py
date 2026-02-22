import azure.durable_functions as df
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from src.utils.config import settings
import logging


@df.DFApp.activity_trigger(input_name="blob_name")
def process_generic_document(blob_name: str) -> dict:
    """Process generic document using Azure Document Intelligence layout model"""
    logging.info(f"Processing generic document: {blob_name}")
    
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
    
    tables = []
    for table in result.tables:
        table_data = {
            "row_count": table.row_count,
            "column_count": table.column_count,
            "cells": [
                {
                    "content": cell.content,
                    "row_index": cell.row_index,
                    "column_index": cell.column_index
                }
                for cell in table.cells
            ]
        }
        tables.append(table_data)
    
    return {
        "document_id": blob_name,
        "document_type": "generic",
        "extracted_data": {"tables": tables},
        "raw_text": result.content,
        "needs_review": False
    }
