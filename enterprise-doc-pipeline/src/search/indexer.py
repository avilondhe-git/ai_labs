from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.core.credentials import AzureKeyCredential
from src.utils.config import settings
import logging


def create_search_index():
    """Create Azure AI Search index with vector search"""
    
    index_client = SearchIndexClient(
        endpoint=settings.SEARCH_ENDPOINT,
        credential=AzureKeyCredential(settings.SEARCH_API_KEY)
    )
    
    fields = [
        SearchField(name="document_id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchField(name="blob_path", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="original_filename", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="document_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="summary", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="key_points", type=SearchFieldDataType.Collection(SearchFieldDataType.String), searchable=True),
        
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="vector-profile"
        ),
        
        SearchField(name="uploaded_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SearchField(name="created_by", type=SearchFieldDataType.String, filterable=True),
    ]
    
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
        profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-algo")]
    )
    
    index = SearchIndex(
        name=settings.SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=vector_search
    )
    
    try:
        index_client.create_index(index)
        logging.info(f"Created index: {settings.SEARCH_INDEX_NAME}")
    except Exception as e:
        logging.warning(f"Index may already exist: {e}")


def index_document(document_data: dict):
    """Index document in Azure AI Search"""
    
    search_client = SearchClient(
        endpoint=settings.SEARCH_ENDPOINT,
        index_name=settings.SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(settings.SEARCH_API_KEY)
    )
    
    search_doc = {
        "document_id": document_data["document_id"],
        "blob_path": document_data.get("blob_path", ""),
        "original_filename": document_data.get("original_filename", ""),
        "document_type": document_data["document_type"],
        "content": document_data.get("raw_text", "")[:10000],
        "summary": document_data.get("summary", ""),
        "key_points": document_data.get("key_points", []),
        "content_vector": document_data.get("embeddings", []),
        "uploaded_at": document_data.get("uploaded_at"),
        "created_by": document_data.get("created_by", "system"),
    }
    
    result = search_client.upload_documents(documents=[search_doc])
    logging.info(f"Indexed document: {document_data['document_id']}")
    
    return result


def search_documents(query: str, top: int = 10, use_semantic: bool = True):
    """Search documents using hybrid search (keyword + vector)"""
    from openai import AzureOpenAI
    
    search_client = SearchClient(
        endpoint=settings.SEARCH_ENDPOINT,
        index_name=settings.SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(settings.SEARCH_API_KEY)
    )
    
    openai_client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION
    )
    
    embedding_response = openai_client.embeddings.create(
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=query
    )
    query_vector = embedding_response.data[0].embedding
    
    results = search_client.search(
        search_text=query,
        vector_queries=[{
            "vector": query_vector,
            "k_nearest_neighbors": top,
            "fields": "content_vector"
        }],
        select=["document_id", "original_filename", "summary", "document_type"],
        top=top
    )
    
    return list(results)
