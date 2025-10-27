#!/bin/bash
# Azure Credentials Setup Script for GitHub Actions
# This script helps you get the AZURE_CREDENTIALS for GitHub Actions

echo "🔧 Azure Credentials Setup for GitHub Actions"
echo "=============================================="
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed."
    echo "Please install Azure CLI first:"
    echo "  Windows: winget install Microsoft.AzureCLI"
    echo "  macOS: brew install azure-cli"
    echo "  Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    exit 1
fi

echo "✅ Azure CLI is installed"
echo ""

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo "🔐 Please login to Azure first:"
    echo "   az login"
    exit 1
fi

echo "✅ You are logged in to Azure"
echo ""

# Get subscription info
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
SUBSCRIPTION_NAME=$(az account show --query name --output tsv)

echo "📋 Current Azure Subscription:"
echo "   ID: $SUBSCRIPTION_ID"
echo "   Name: $SUBSCRIPTION_NAME"
echo ""

# Get resource group name
echo "📁 Available Resource Groups:"
az group list --query "[].name" --output table
echo ""

read -p "Enter your resource group name (e.g., quantum-blue-rg): " RESOURCE_GROUP

# Verify resource group exists
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo "❌ Resource group '$RESOURCE_GROUP' not found."
    echo "Please create it first:"
    echo "   az group create --name '$RESOURCE_GROUP' --location 'East US'"
    exit 1
fi

echo "✅ Resource group '$RESOURCE_GROUP' found"
echo ""

# Create service principal
echo "🔑 Creating service principal for GitHub Actions..."
echo "This will create a service principal with Contributor role on your resource group."
echo ""

SP_NAME="quantum-blue-github-actions"
SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"

echo "Creating service principal: $SP_NAME"
echo "Scope: $SCOPE"
echo ""

# Create the service principal and get credentials
CREDENTIALS=$(az ad sp create-for-rbac --name "$SP_NAME" --role contributor --scopes "$SCOPE" --sdk-auth)

if [ $? -eq 0 ]; then
    echo "✅ Service principal created successfully!"
    echo ""
    echo "🔐 AZURE_CREDENTIALS for GitHub Secrets:"
    echo "=========================================="
    echo "$CREDENTIALS"
    echo ""
    echo "📋 Instructions:"
    echo "1. Go to your GitHub repository: https://github.com/MahendraMedapati27/Data_Management_Chatbot"
    echo "2. Click Settings → Secrets and variables → Actions"
    echo "3. Click 'New repository secret'"
    echo "4. Name: AZURE_CREDENTIALS"
    echo "5. Value: (paste the JSON above)"
    echo "6. Click 'Add secret'"
    echo ""
    echo "7. Add another secret:"
    echo "   Name: AZURE_RESOURCE_GROUP"
    echo "   Value: $RESOURCE_GROUP"
    echo ""
    echo "🎉 After adding these secrets, your GitHub Actions workflow will work!"
else
    echo "❌ Failed to create service principal"
    echo "Please check your Azure permissions and try again"
fi
