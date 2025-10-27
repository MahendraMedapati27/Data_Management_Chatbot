# 🔧 Azure Credentials Fix Script
# This script creates proper Azure credentials for GitHub Actions

Write-Host "🔧 Fixing Azure Credentials for GitHub Actions" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Check if Azure CLI is installed
try {
    $null = Get-Command az -ErrorAction Stop
    Write-Host "✅ Azure CLI is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI is not installed." -ForegroundColor Red
    Write-Host "Please install Azure CLI first:" -ForegroundColor Yellow
    Write-Host "  Windows: winget install Microsoft.AzureCLI" -ForegroundColor Cyan
    exit 1
}

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
$tenantId = az account show --query tenantId --output tsv

Write-Host "📋 Current Azure Subscription:" -ForegroundColor Cyan
Write-Host "   ID: $subscriptionId" -ForegroundColor White
Write-Host "   Name: $subscriptionName" -ForegroundColor White
Write-Host "   Tenant ID: $tenantId" -ForegroundColor White
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

# Delete existing service principal if it exists
$spName = "quantum-blue-github-actions"
Write-Host "🗑️  Cleaning up existing service principal (if any)..." -ForegroundColor Yellow
try {
    $existingSp = az ad sp list --display-name $spName --query "[0].appId" --output tsv
    if ($existingSp) {
        az ad sp delete --id $existingSp 2>$null
        Write-Host "✅ Removed existing service principal" -ForegroundColor Green
    }
} catch {
    Write-Host "ℹ️  No existing service principal found" -ForegroundColor Blue
}

Write-Host ""

# Create new service principal with proper permissions
Write-Host "🔑 Creating new service principal for GitHub Actions..." -ForegroundColor Yellow
Write-Host "This will create a service principal with Contributor role on your resource group." -ForegroundColor Yellow
Write-Host ""

$scope = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup"

Write-Host "Creating service principal: $spName" -ForegroundColor Cyan
Write-Host "Scope: $scope" -ForegroundColor Cyan
Write-Host ""

# Create the service principal and get credentials
Write-Host "⏳ Creating service principal (this may take a moment)..." -ForegroundColor Yellow
$credentials = az ad sp create-for-rbac --name $spName --role contributor --scopes $scope --sdk-auth

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Service principal created successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Parse the JSON to verify it has all required fields
    try {
        $credObj = $credentials | ConvertFrom-Json
        $requiredFields = @('clientId', 'clientSecret', 'subscriptionId', 'tenantId')
        $missingFields = @()
        
        foreach ($field in $requiredFields) {
            if (-not $credObj.$field) {
                $missingFields += $field
            }
        }
        
        if ($missingFields.Count -gt 0) {
            Write-Host "❌ Generated credentials are missing required fields: $($missingFields -join ', ')" -ForegroundColor Red
            Write-Host "Let's try an alternative approach..." -ForegroundColor Yellow
            Write-Host ""
            
            # Alternative approach: Create SP manually and get credentials
            Write-Host "🔧 Creating service principal manually..." -ForegroundColor Yellow
            
            # Create app registration
            $app = az ad app create --display-name $spName --output json | ConvertFrom-Json
            $appId = $app.appId
            
            # Create service principal
            az ad sp create --id $appId --output none
            
            # Create password/secret
            $secret = az ad app credential reset --id $appId --output json | ConvertFrom-Json
            
            # Assign role
            az role assignment create --assignee $appId --role "Contributor" --scope $scope --output none
            
            # Create proper credentials JSON
            $credentials = @{
                clientId = $appId
                clientSecret = $secret.password
                subscriptionId = $subscriptionId
                tenantId = $tenantId
                activeDirectoryEndpointUrl = "https://login.microsoftonline.com"
                resourceManagerEndpointUrl = "https://management.azure.com/"
                activeDirectoryGraphResourceId = "https://graph.windows.net/"
                sqlManagementEndpointUrl = "https://management.core.windows.net:8443/"
                galleryEndpointUrl = "https://gallery.azure.com/"
                managementEndpointUrl = "https://management.core.windows.net/"
            } | ConvertTo-Json -Depth 10
            
            Write-Host "✅ Service principal created manually with all required fields!" -ForegroundColor Green
        }
        
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
        Write-Host "8. Verify the JSON contains these fields:" -ForegroundColor Cyan
        Write-Host "   - clientId" -ForegroundColor White
        Write-Host "   - clientSecret" -ForegroundColor White
        Write-Host "   - subscriptionId" -ForegroundColor White
        Write-Host "   - tenantId" -ForegroundColor White
        Write-Host ""
        Write-Host "🎉 After adding these secrets, your GitHub Actions workflow will work!" -ForegroundColor Green
        
    } catch {
        Write-Host "❌ Error parsing credentials JSON" -ForegroundColor Red
        Write-Host "Please try running the script again" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Failed to create service principal" -ForegroundColor Red
    Write-Host "Please check your Azure permissions and try again" -ForegroundColor Yellow
}
