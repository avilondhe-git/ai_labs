# Azure RAG Document Intelligence System

> Production-ready RAG system using Azure AI services

## 🎯 What This Does

Enterprise-grade Retrieval Augmented Generation (RAG) system that:
- Stores documents in **Azure Blob Storage**
- Generates embeddings with **Azure OpenAI**
- Indexes with **Azure AI Search** (hybrid search)
- Answers questions using **GPT-4o-mini**

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Documents   │────▶│  Azure Blob     │────▶│  Document        │
│  (PDFs)      │     │  Storage        │     │  Loader          │
└──────────────┘     └─────────────────┘     └────────┬─────────┘
                                                       │
                                                       ▼
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Streamlit   │◀────│  RAG Chain      │◀────│  Embedding       │
│  UI          │     │  (GPT-4o-mini)  │     │  Pipeline        │
└──────────────┘     └────────┬────────┘     └────────┬─────────┘
                              │                        │
                              ▼                        ▼
                     ┌─────────────────┐     ┌──────────────────┐
                     │  Hybrid         │◀────│  Azure AI        │
                     │  Retriever      │     │  Search Index    │
                     └─────────────────┘     └──────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.10+
- Azure subscription ([Get $200 free credit](https://azure.microsoft.com/free/))
- Azure CLI installed

### 1. Setup Environment

```bash
# Clone and navigate
cd AIPoC/code/01.AZ_rag_poc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Azure Resources

```bash
# Login to Azure
az login

# Run setup script
chmod +x setup_azure.sh
./setup_azure.sh
```

This creates:
- Resource Group
- Storage Account with container
- Azure OpenAI Service (with models deployed)
- Azure AI Search Service

### 3. Configure Environment

```bash
# Copy generated config
cp azure_config.env .env

# Verify configuration
cat .env
```

### 4. Upload Sample Documents

```bash
# Generate test documents or add your own PDFs to data/sample/
python tests/generate_test_data.py

# Upload to Azure Blob Storage
python src/azure_blob_loader.py
```

### 5. Create Search Index

```bash
# Generate embeddings and create index
python src/azure_search_manager.py
```

### 6. Test RAG Chain

```bash
# Test query pipeline
python src/rag_chain.py
```

### 7. Launch Web UI

```bash
# Start Streamlit app
streamlit run src/streamlit_app.py
```

Open browser to http://localhost:8501

## Usage Examples

### Command Line

```python
from src.rag_chain import RAGChain

rag = RAGChain()
response = rag.query("What is retrieval augmented generation?")

print(response["answer"])
print(f"Sources: {len(response['sources'])}")
```

### Web UI

1. Open http://localhost:8501
2. Type question: "What is RAG?"
3. View answer with source citations
4. Expand sources to see original text

## Features

- **Hybrid Search**: Vector (semantic) + Keyword (BM25)
- **Source Citations**: Every answer includes source documents
- **Metadata Tracking**: File names, page numbers, relevance scores
- **Cost Monitoring**: Token usage tracking
- **Error Handling**: Graceful failures with logging
- **Scalable**: Handles 1000s of documents

## 🔧 Configuration

Edit `.env` file:

```env
# Adjust chunk size for your documents
CHUNK_SIZE=1000          # Characters per chunk
CHUNK_OVERLAP=200        # Overlap between chunks

# Control retrieval
TOP_K_RESULTS=4          # Number of documents to retrieve

# Logging
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR
```

## 💰 Cost Breakdown

**Development (1 month):**
- Storage: ~$1
- Azure OpenAI: ~$5-10
- AI Search (Basic): ~$73
- **Total: ~$80/month**

**Production (per month):**
- 10K queries/day
- Storage: ~$2
- OpenAI: ~$150-200
- AI Search (Standard): ~$250
- **Total: ~$400-450/month**

**Cost Optimization:**
1. Use Azure $200 free credit
2. Delete resources when not in use
3. Use Basic tier for development
4. Implement caching for common queries

## 🧪 Testing

```bash
# Test individual components
python src/azure_blob_loader.py      # Document loading
python src/embedding_pipeline.py     # Embedding generation
python src/retriever.py              # Hybrid search
python src/rag_chain.py              # Complete pipeline

# Run all tests
pytest tests/
```

## 📁 Project Structure

```
01.AZ_rag_poc/
├── src/
│   ├── azure_blob_loader.py       # Document loading from Blob Storage
│   ├── embedding_pipeline.py      # Chunking + embedding generation
│   ├── azure_search_manager.py    # Index creation and management
│   ├── retriever.py               # Hybrid search retrieval
│   ├── rag_chain.py               # Complete RAG pipeline
│   ├── streamlit_app.py           # Web UI
│   └── utils/
│       ├── config.py              # Configuration management
│       └── logger.py              # Logging setup
├── tests/
│   ├── generate_test_data.py      # Generate sample PDFs
│   └── test_pipeline.py           # Integration tests
├── data/
│   ├── sample/                    # Sample PDFs (for testing)
│   ├── raw/                       # Input documents
│   └── processed/                 # Processed outputs
├── configs/
│   ├── index_schema.json          # Search index schema
│   └── search_config.json         # Search configuration
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
├── setup_azure.sh                 # Azure resource setup script
└── README.md                      # This file
```

## 🔒 Security

**Best Practices:**
- Use Azure Managed Identity (no keys in code)
- Enable Private Link for Azure services
- Store secrets in Azure Key Vault
- Use RBAC for access control
- Enable Azure Monitor for audit logs

**For Production:**
```bash
# Use Managed Identity instead of API keys
az identity create --name mi-rag-poc --resource-group $RESOURCE_GROUP

# Assign roles
az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role "Cognitive Services User" \
  --scope <azure-openai-resource-id>
```

## 🐛 Troubleshooting

### Issue: "No module named 'src'"
```bash
# Make sure you're in the project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "Failed to connect to Azure OpenAI"
```bash
# Verify endpoint and key
az cognitiveservices account show \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP
```

### Issue: "Index not found"
```bash
# Recreate index
python src/azure_search_manager.py
```

### Issue: "High costs"
```bash
# Check spending
az consumption usage list --start-date 2024-01-01

# Delete resources
az group delete --name $RESOURCE_GROUP --yes
```

## 🧹 Cleanup

**Delete all resources:**
```bash
az group delete --name rg-rag-poc --yes --no-wait
```

**Verify deletion:**
```bash
az group list --output table
```

## Learn More

- [Implementation Guide](../../docs-rdm/01.AZ_rag_poc_implementation.md) - Step-by-step instructions
- [Architecture Guide](../../docs-rdm/01.AZ_rag_poc_guide.md) - Azure design patterns
- [Comparison Guide](../../docs-rdm/01_rag_comparison.md) - LangChain vs Azure

**Azure Documentation:**
- [Azure AI Search](https://learn.microsoft.com/en-us/azure/search/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

## 🤝 Contributing

This is a learning project. Feel free to:
- Add new features
- Improve documentation
- Optimize costs
- Share learnings

## 📄 License

MIT License - feel free to use for learning and portfolio projects.

---

**Built with Azure AI Services** ☁️
