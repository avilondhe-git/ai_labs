#!/bin/bash

# Azure RAG PoC - Resource Setup Script
# This script creates all required Azure resources for the RAG system

set -e  # Exit on error

echo "Azure RAG PoC - Resource Setup"
echo "=================================="

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run: az login"
    exit 1
fi

echo "Azure CLI authenticated"

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-rag-poc}"
LOCATION="${LOCATION:-eastus}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-storageragpoc$(openssl rand -hex 3)}"
OPENAI_SERVICE="${OPENAI_SERVICE:-openai-rag-poc}"
SEARCH_SERVICE="${SEARCH_SERVICE:-search-rag-poc-$(openssl rand -hex 3)}"

echo ""
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  OpenAI Service: $OPENAI_SERVICE"
echo "  Search Service: $SEARCH_SERVICE"
echo ""

read -p "Continue with these settings? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Create Resource Group
echo ""
echo "📦 Creating Resource Group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output none

echo "Resource group created"

# Create Storage Account
echo ""
echo "💾 Creating Storage Account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --output none

echo "Storage account created"

# Get connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv)

# Create container
echo "  Creating documents container..."
az storage container create \
  --name documents \
  --connection-string "$STORAGE_CONNECTION_STRING" \
  --output none

echo "Container created"

# Create Azure OpenAI Service
echo ""
echo "🤖 Creating Azure OpenAI Service..."
az cognitiveservices account create \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --kind OpenAI \
  --sku S0 \
  --yes \
  --output none

echo "Azure OpenAI service created"

# Get OpenAI endpoint and key
OPENAI_ENDPOINT=$(az cognitiveservices account show \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint -o tsv)

OPENAI_API_KEY=$(az cognitiveservices account keys list \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --query key1 -o tsv)

# Deploy OpenAI Models
echo ""
echo "Deploying OpenAI Models..."

echo "  Deploying text-embedding-ada-002..."
az cognitiveservices account deployment create \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard \
  --output none

echo "  Deploying gpt-4o-mini..."
az cognitiveservices account deployment create \
  --name $OPENAI_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4o-mini \
  --model-name gpt-4o-mini \
  --model-version "2024-07-18" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard \
  --output none

echo "Models deployed"

# Create Azure AI Search
echo ""
echo "Creating Azure AI Search Service..."
az search service create \
  --name $SEARCH_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku basic \
  --output none

echo "AI Search service created"

# Get Search admin key
SEARCH_ADMIN_KEY=$(az search admin-key show \
  --service-name $SEARCH_SERVICE \
  --resource-group $RESOURCE_GROUP \
  --query primaryKey -o tsv)

SEARCH_ENDPOINT="https://${SEARCH_SERVICE}.search.windows.net"

# Save configuration to azure_config.env
echo ""
echo "💾 Saving configuration..."

cat > azure_config.env << EOF
# Azure Resource Configuration
# Generated: $(date)

RESOURCE_GROUP=$RESOURCE_GROUP
STORAGE_ACCOUNT=$STORAGE_ACCOUNT
STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION_STRING
OPENAI_ENDPOINT=$OPENAI_ENDPOINT
OPENAI_API_KEY=$OPENAI_API_KEY
SEARCH_ENDPOINT=$SEARCH_ENDPOINT
SEARCH_ADMIN_KEY=$SEARCH_ADMIN_KEY
EOF

echo "Configuration saved to azure_config.env"

# Create .env file from template
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    
    cp .env.example .env
    
    # Use sed to replace placeholders
    sed -i.bak "s|your_storage_connection_string|$STORAGE_CONNECTION_STRING|g" .env
    sed -i.bak "s|https://your-openai.openai.azure.com/|$OPENAI_ENDPOINT|g" .env
    sed -i.bak "s|your_openai_api_key_here|$OPENAI_API_KEY|g" .env
    sed -i.bak "s|https://your-search.search.windows.net|$SEARCH_ENDPOINT|g" .env
    sed -i.bak "s|your_search_admin_key_here|$SEARCH_ADMIN_KEY|g" .env
    
    rm .env.bak
    
    echo ".env file created"
fi

# Summary
echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Resources created:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  Blob Container: documents"
echo "  Azure OpenAI: $OPENAI_SERVICE"
echo "    - text-embedding-ada-002 (deployed)"
echo "    - gpt-4o-mini (deployed)"
echo "  Azure AI Search: $SEARCH_SERVICE"
echo ""
echo "Configuration files:"
echo "  azure_config.env (backup config)"
echo "  .env (application config)"
echo ""
echo "Next steps:"
echo "  1. Review .env file"
echo "  2. Upload documents: python src/azure_blob_loader.py"
echo "  3. Create index: python src/azure_search_manager.py"
echo "  4. Test system: python src/rag_chain.py"
echo "  5. Launch UI: streamlit run src/streamlit_app.py"
echo ""
echo "💰 Estimated monthly cost: ~$73-80 (Basic tier)"
echo "Don't forget to delete resources when done:"
echo "    az group delete --name $RESOURCE_GROUP --yes"
echo ""
