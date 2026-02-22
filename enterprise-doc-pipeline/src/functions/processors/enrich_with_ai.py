import azure.durable_functions as df
from openai import AzureOpenAI
from src.utils.config import settings
import logging


@df.DFApp.activity_trigger(input_name="extracted_data")
def enrich_with_ai(extracted_data: dict) -> dict:
    """Enrich document with AI-generated summary and embeddings"""
    logging.info(f"Enriching document: {extracted_data['document_id']}")
    
    client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION
    )
    
    raw_text = extracted_data.get("raw_text", "")
    
    summary_response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "Summarize this document in 2-3 sentences, focusing on key information, dates, amounts, and parties involved."},
            {"role": "user", "content": raw_text[:4000]}
        ],
        temperature=0.3
    )
    summary = summary_response.choices[0].message.content
    
    keypoints_response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "Extract 3-5 key points from this document as a bullet list."},
            {"role": "user", "content": raw_text[:4000]}
        ],
        temperature=0.3
    )
    key_points = keypoints_response.choices[0].message.content.split('\n')
    key_points = [kp.strip('- •').strip() for kp in key_points if kp.strip()]
    
    embedding_response = client.embeddings.create(
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=raw_text[:8000]
    )
    embeddings = embedding_response.data[0].embedding
    
    extracted_data["summary"] = summary
    extracted_data["key_points"] = key_points
    extracted_data["embeddings"] = embeddings
    
    return extracted_data
