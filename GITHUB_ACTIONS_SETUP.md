# 🔧 GitHub Actions Azure Deployment Setup Guide

## 🚨 Issue Resolved: Missing Azure Credentials

The GitHub Actions workflow was failing because it was missing Azure authentication credentials. I've updated the workflow file to include proper Azure login.

---

## 🔑 Required GitHub Secrets Setup

You need to add these secrets to your GitHub repository:

### 1. Go to GitHub Repository Settings
1. Navigate to: https://github.com/MahendraMedapati27/Data_Management_Chatbot
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### 2. Add Required Secrets

#### Secret 1: AZURE_CREDENTIALS
**Name**: `AZURE_CREDENTIALS`
**Value**: (See below for how to get this)

#### Secret 2: AZURE_RESOURCE_GROUP
**Name**: `AZURE_RESOURCE_GROUP`
**Value**: `quantum-blue-rg` (or your resource group name)

---

## 🔐 How to Get AZURE_CREDENTIALS

### Method 1: Using Azure CLI (Recommended)

1. **Install Azure CLI** (if not already installed):
   ```bash
   # Windows
   winget install Microsoft.AzureCLI
   
   # Or download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
   ```

2. **Login to Azure**:
   ```bash
   az login
   ```

3. **Create Service Principal**:
   ```bash
   az ad sp create-for-rbac --name "quantum-blue-github-actions" --role contributor --scopes /subscriptions/{subscription-id}/resourceGroups/quantum-blue-rg --sdk-auth
   ```

4. **Copy the JSON output** - this is your `AZURE_CREDENTIALS` secret value.

### Method 2: Using Azure Portal

1. **Go to Azure Portal** → **Azure Active Directory** → **App registrations**
2. **Click "New registration"**
3. **Name**: `quantum-blue-github-actions`
4. **Click "Register"**
5. **Go to "Certificates & secrets"** → **New client secret**
6. **Copy the secret value**
7. **Go to "API permissions"** → **Add permission** → **Azure Service Management** → **Delegated permissions** → **user_impersonation**
8. **Grant admin consent**

---

## 📋 Step-by-Step Setup Instructions

### Step 1: Create Azure Resources (if not done already)

```bash
# Login to Azure
az login

# Create resource group
az group create --name "quantum-blue-rg" --location "East US"

# Create app service plan
az appservice plan create --name "quantum-blue-plan" --resource-group "quantum-blue-rg" --sku "B1" --is-linux

# Create web app
az webapp create --resource-group "quantum-blue-rg" --plan "quantum-blue-plan" --name "quantum-blue-chatbot" --runtime "PYTHON|3.9"
```

### Step 2: Get Your Subscription ID

```bash
az account show --query id --output tsv
```

### Step 3: Create Service Principal

```bash
# Replace {subscription-id} with your actual subscription ID
az ad sp create-for-rbac --name "quantum-blue-github-actions" --role contributor --scopes /subscriptions/{subscription-id}/resourceGroups/quantum-blue-rg --sdk-auth
```

**Example output**:
```json
{
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "your-client-secret",
  "subscriptionId": "87654321-4321-4321-4321-210987654321",
  "tenantId": "11111111-2222-3333-4444-555555555555",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### Step 4: Add GitHub Secrets

1. **Go to GitHub Repository**: https://github.com/MahendraMedapati27/Data_Management_Chatbot
2. **Settings** → **Secrets and variables** → **Actions**
3. **Add these secrets**:

   **Secret 1**:
   - **Name**: `AZURE_CREDENTIALS`
   - **Value**: (The entire JSON output from Step 3)

   **Secret 2**:
   - **Name**: `AZURE_RESOURCE_GROUP`
   - **Value**: `quantum-blue-rg`

### Step 5: Commit and Push Changes

```bash
git add .github/workflows/azure-deploy.yml
git commit -m "Fix GitHub Actions workflow with Azure authentication"
git push origin main
```

---

## 🧪 Test the Deployment

### 1. Trigger the Workflow
- Go to your GitHub repository
- Click **Actions** tab
- You should see the workflow running
- Click on the latest run to monitor progress

### 2. Check Deployment Status
- The workflow should now complete successfully
- Your app will be deployed to: `https://quantum-blue-chatbot.azurewebsites.net`

### 3. Verify App is Running
```bash
# Check if the app is running
curl https://quantum-blue-chatbot.azurewebsites.net/health

# Expected response:
# {"status": "healthy", "service": "quantum-blue-chatbot"}
```

---

## 🔧 Alternative Deployment Methods

If you prefer not to use GitHub Actions, you can deploy manually:

### Method 1: Direct Azure Deployment
```bash
# Deploy directly from local machine
az webapp deployment source config --resource-group "quantum-blue-rg" --name "quantum-blue-chatbot" --repo-url "https://github.com/MahendraMedapati27/Data_Management_Chatbot.git" --branch main --manual-integration
```

### Method 2: Using Azure Portal
1. Go to Azure Portal
2. Navigate to your App Service
3. Go to **Deployment Center**
4. Select **GitHub** as source
5. Authorize and select your repository
6. Deploy

---

## 🚨 Troubleshooting

### Issue: "No credentials found"
**Solution**: Make sure you've added the `AZURE_CREDENTIALS` secret to GitHub

### Issue: "Resource group not found"
**Solution**: Check that `AZURE_RESOURCE_GROUP` secret matches your actual resource group name

### Issue: "Permission denied"
**Solution**: Ensure the service principal has Contributor role on the resource group

### Issue: "App deployment failed"
**Solution**: Check Azure logs and ensure all environment variables are set

---

## 📊 Monitoring Deployment

### GitHub Actions Logs
- Go to **Actions** tab in your repository
- Click on the latest workflow run
- Check each step for errors

### Azure App Service Logs
```bash
# View real-time logs
az webapp log tail --name quantum-blue-chatbot --resource-group quantum-blue-rg

# Download logs
az webapp log download --name quantum-blue-chatbot --resource-group quantum-blue-rg
```

---

## ✅ Verification Checklist

- [ ] Azure resources created (Resource Group, App Service Plan, Web App)
- [ ] Service principal created with Contributor role
- [ ] GitHub secrets added (`AZURE_CREDENTIALS`, `AZURE_RESOURCE_GROUP`)
- [ ] Workflow file updated and committed
- [ ] GitHub Actions workflow runs successfully
- [ ] App is accessible at `https://quantum-blue-chatbot.azurewebsites.net`
- [ ] Health check endpoint responds correctly

---

## 🎯 Next Steps After Successful Deployment

1. **Set Environment Variables** in Azure Portal
2. **Configure WhatsApp Business API**
3. **Set up custom domain** (optional)
4. **Enable Application Insights** for monitoring
5. **Set up alerts** for errors and performance

---

**🎉 Once you've added the GitHub secrets, your deployment should work perfectly!**
