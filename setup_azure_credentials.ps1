# Azure Credentials Setup Script for GitHub Actions (PowerShell)
# This script helps you get the AZURE_CREDENTIALS for GitHub Actions

Write-Host "🔧 Azure Credentials Setup for GitHub Actions" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""

# Check if Azure CLI is installed
try {
    $null = Get-Command az -ErrorAction Stop
    Write-Host "✅ Azure CLI is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI is not installed." -ForegroundColor Red
    Write-Host "Please install Azure CLI first:" -ForegroundColor Yellow
    Write-Host "  Windows: winget install Microsoft.AzureCLI" -ForegroundColor Cyan
    Write-Host "  Or download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# Check if user is logged in
try {
    $null = az account show 2>$null
    Write-Host "✅ You are logged in to Azure" -ForegroundColor Green
} catch {
    Write-Host "🔐 Please login to Azure first:" -ForegroundColor Yellow
    Write-Host "   az login" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# Get subscription info
$subscriptionId = az account show --query id --output tsv
$subscriptionName = az account show --query name --output tsv

Write-Host "📋 Current Azure Subscription:" -ForegroundColor Cyan
Write-Host "   ID: $subscriptionId" -ForegroundColor White
Write-Host "   Name: $subscriptionName" -ForegroundColor White
Write-Host ""

# Get resource group name
Write-Host "📁 Available Resource Groups:" -ForegroundColor Cyan
az group list --query "[].name" --output table
Write-Host ""

$resourceGroup = Read-Host "Enter your resource group name (e.g., quantum-blue-rg)"

# Verify resource group exists
try {
    $null = az group show --name $resourceGroup 2>$null
    Write-Host "✅ Resource group '$resourceGroup' found" -ForegroundColor Green
} catch {
    Write-Host "❌ Resource group '$resourceGroup' not found." -ForegroundColor Red
    Write-Host "Please create it first:" -ForegroundColor Yellow
    Write-Host "   az group create --name '$resourceGroup' --location 'East US'" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# Create service principal
Write-Host "🔑 Creating service principal for GitHub Actions..." -ForegroundColor Yellow
Write-Host "This will create a service principal with Contributor role on your resource group." -ForegroundColor Yellow
Write-Host ""

$spName = "quantum-blue-github-actions"
$scope = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup"

Write-Host "Creating service principal: $spName" -ForegroundColor Cyan
Write-Host "Scope: $scope" -ForegroundColor Cyan
Write-Host ""

# Create the service principal and get credentials
$credentials = az ad sp create-for-rbac --name $spName --role contributor --scopes $scope --sdk-auth

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Service principal created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔐 AZURE_CREDENTIALS for GitHub Secrets:" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host $credentials -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Instructions:" -ForegroundColor Cyan
    Write-Host "1. Go to your GitHub repository: https://github.com/MahendraMedapati27/Data_Management_Chatbot" -ForegroundColor White
    Write-Host "2. Click Settings → Secrets and variables → Actions" -ForegroundColor White
    Write-Host "3. Click 'New repository secret'" -ForegroundColor White
    Write-Host "4. Name: AZURE_CREDENTIALS" -ForegroundColor White
    Write-Host "5. Value: (paste the JSON above)" -ForegroundColor White
    Write-Host "6. Click 'Add secret'" -ForegroundColor White
    Write-Host ""
    Write-Host "7. Add another secret:" -ForegroundColor Cyan
    Write-Host "   Name: AZURE_RESOURCE_GROUP" -ForegroundColor White
    Write-Host "   Value: $resourceGroup" -ForegroundColor White
    Write-Host ""
    Write-Host "🎉 After adding these secrets, your GitHub Actions workflow will work!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create service principal" -ForegroundColor Red
    Write-Host "Please check your Azure permissions and try again" -ForegroundColor Yellow
}
