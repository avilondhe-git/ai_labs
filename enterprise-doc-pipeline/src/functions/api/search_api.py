from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from src.search.indexer import search_documents
from src.utils.cosmos_client import DocumentStore
import logging

app = FastAPI(title="Document Search API")

logger = logging.getLogger(__name__)


@app.get("/search")
async def search(
    query: str = Query(..., description="Search query"),
    top: int = Query(10, ge=1, le=100, description="Number of results")
):
    """Search documents using hybrid search"""
    try:
        results = search_documents(query, top=top)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/document/{document_id}")
async def get_document(document_id: str):
    """Retrieve document metadata by ID"""
    try:
        store = DocumentStore()
        document = store.get_document(document_id)
        return document.model_dump()
    except Exception as e:
        logger.error(f"Document retrieval error: {e}")
        raise HTTPException(status_code=404, detail="Document not found")


@app.get("/documents/by-type")
async def get_documents_by_type(document_type: str):
    """Query documents by type"""
    try:
        store = DocumentStore()
        query = f"SELECT * FROM c WHERE c.document_type = '{document_type}'"
        documents = store.query_documents(query)
        return {
            "document_type": document_type,
            "documents": [doc.model_dump() for doc in documents],
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
