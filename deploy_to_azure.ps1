# Azure App Service Deployment Script (PowerShell)
# This script helps deploy the chatbot to Azure App Service

# Step 1: Create Azure App Service
Write-Host "Creating Azure App Service..." -ForegroundColor Green
az webapp create --resource-group "your-resource-group" --plan "your-app-service-plan" --name "quantum-blue-chatbot" --runtime "PYTHON|3.9"

# Step 2: Configure App Settings
Write-Host "Configuring App Settings..." -ForegroundColor Green
az webapp config appsettings set --resource-group "your-resource-group" --name "quantum-blue-chatbot" --settings `
  FLASK_ENV=production `
  FLASK_DEBUG=false `
  FLASK_HOST=0.0.0.0 `
  FLASK_PORT=8000 `
  PYTHONUNBUFFERED=1 `
  WEBSITE_PYTHON_DEFAULT_VERSION=3.9 `
  WEBSITE_SKIP_CONTENTSHARE_VALIDATION=1 `
  WEBSITE_RUN_FROM_PACKAGE=0

# Step 3: Configure GitHub Deployment
Write-Host "Configuring GitHub deployment..." -ForegroundColor Green
az webapp deployment source config --resource-group "your-resource-group" --name "quantum-blue-chatbot" `
  --repo-url "https://github.com/MahendraMedapati27/Data_Management_Chatbot.git" `
  --branch main `
  --manual-integration

# Step 4: Set up continuous deployment
Write-Host "Setting up continuous deployment..." -ForegroundColor Green
az webapp deployment source config --resource-group "your-resource-group" --name "quantum-blue-chatbot" `
  --repo-url "https://github.com/MahendraMedapati27/Data_Management_Chatbot.git" `
  --branch main `
  --git-token "your-github-token"

Write-Host "Deployment configuration complete!" -ForegroundColor Green
Write-Host "Remember to set your environment variables in Azure App Service Configuration." -ForegroundColor Yellow
