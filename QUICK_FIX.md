# Quick Azure Credentials Fix - One Command Solution

## 🚀 One-Line Command to Fix Azure Credentials

Run this single command to get the correct Azure credentials for GitHub Actions:

```bash
az ad sp create-for-rbac --name "quantum-blue-github-actions" --role contributor --scopes "/subscriptions/$(az account show --query id --output tsv)/resourceGroups/quantum-blue-rg" --sdk-auth
```

**Replace `quantum-blue-rg` with your actual resource group name if different.**

---

## 📋 Step-by-Step Instructions

### 1. Run the Command
Copy and paste the command above into your terminal (PowerShell or Bash).

### 2. Copy the Output
The command will output a JSON like this:
```json
{
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "your-secret-here",
  "subscriptionId": "87654321-4321-4321-4321-210987654321",
  "tenantId": "11111111-2222-3333-4444-555555555555",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### 3. Add GitHub Secrets
1. Go to: https://github.com/MahendraMedapati27/Data_Management_Chatbot/settings/secrets/actions
2. Click "New repository secret"
3. Add these secrets:

   **Secret 1:**
   - Name: `AZURE_CREDENTIALS`
   - Value: (The entire JSON output from step 2)

   **Secret 2:**
   - Name: `AZURE_RESOURCE_GROUP`
   - Value: `quantum-blue-rg`

### 4. Test Deployment
1. Go to your GitHub repository
2. Click "Actions" tab
3. The workflow should now run successfully

---

## 🔧 If the Command Fails

### Error: "Resource group not found"
Create the resource group first:
```bash
az group create --name "quantum-blue-rg" --location "East US"
```

### Error: "Permission denied"
Make sure you have the right permissions in Azure:
```bash
az login
az account show
```

### Error: "Service principal already exists"
Delete the existing one first:
```bash
az ad sp delete --id $(az ad sp list --display-name "quantum-blue-github-actions" --query "[0].appId" --output tsv)
```

---

## ✅ Verification

Your JSON should have these exact field names:
- `clientId` ✅
- `clientSecret` ✅
- `subscriptionId` ✅
- `tenantId` ✅
- `activeDirectoryEndpointUrl` ✅
- `resourceManagerEndpointUrl` ✅
- `activeDirectoryGraphResourceId` ✅
- `sqlManagementEndpointUrl` ✅
- `galleryEndpointUrl` ✅
- `managementEndpointUrl` ✅

---

**🎉 This should resolve your GitHub Actions deployment issue!**
