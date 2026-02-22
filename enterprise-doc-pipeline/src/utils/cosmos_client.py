from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from src.utils.config import settings
from src.models.document import DocumentMetadata
import logging


class DocumentStore:
    """Cosmos DB client for document metadata"""
    
    def __init__(self):
        if settings.COSMOS_KEY:
            self.client = CosmosClient(settings.COSMOS_ENDPOINT, settings.COSMOS_KEY)
        else:
            self.client = CosmosClient(settings.COSMOS_ENDPOINT, DefaultAzureCredential())
        
        self.database = self.client.get_database_client(settings.COSMOS_DATABASE_NAME)
        self.container = self.database.get_container_client(settings.COSMOS_CONTAINER_NAME)
    
    def create_document(self, metadata: DocumentMetadata):
        """Store document metadata"""
        doc_dict = metadata.model_dump(mode='json')
        self.container.upsert_item(doc_dict)
        logging.info(f"Stored metadata for: {metadata.document_id}")
    
    def get_document(self, document_id: str) -> DocumentMetadata:
        """Retrieve document metadata"""
        item = self.container.read_item(item=document_id, partition_key=document_id)
        return DocumentMetadata(**item)
    
    def update_status(self, document_id: str, status: str):
        """Update processing status"""
        doc = self.container.read_item(item=document_id, partition_key=document_id)
        doc["status"] = status
        self.container.replace_item(item=document_id, body=doc)
    
    def query_documents(self, query: str):
        """Query documents with SQL"""
        items = self.container.query_items(query=query, enable_cross_partition_query=True)
        return [DocumentMetadata(**item) for item in items]
