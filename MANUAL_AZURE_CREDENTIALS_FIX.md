# 🔧 Manual Azure Credentials Setup Guide

## 🚨 Issue: Missing client-id and tenant-id in AZURE_CREDENTIALS

The GitHub Actions workflow is failing because the `AZURE_CREDENTIALS` secret is missing required fields. Here's how to fix it:

---

## 🔑 Method 1: Using the Fix Script (Recommended)

Run the PowerShell script I created:

```powershell
.\fix_azure_credentials.ps1
```

This script will:
- Clean up any existing service principal
- Create a new one with all required fields
- Generate the complete credentials JSON

---

## 🔑 Method 2: Manual Commands

If the script doesn't work, follow these manual steps:

### Step 1: Login to Azure
```bash
az login
```

### Step 2: Get Your Subscription and Tenant Info
```bash
# Get subscription ID
az account show --query id --output tsv

# Get tenant ID
az account show --query tenantId --output tsv
```

### Step 3: Create Service Principal Manually
```bash
# Replace {subscription-id} with your actual subscription ID
# Replace {resource-group} with your resource group name

# Create app registration
az ad app create --display-name "quantum-blue-github-actions"

# Note the appId from the output, then create service principal
az ad sp create --id {appId}

# Create password/secret
az ad app credential reset --id {appId}

# Assign Contributor role to resource group
az role assignment create --assignee {appId} --role "Contributor" --scope "/subscriptions/{subscription-id}/resourceGroups/{resource-group}"
```

### Step 4: Create Complete Credentials JSON
Create a JSON file with this structure (replace the values):

```json
{
  "clientId": "your-app-id",
  "clientSecret": "your-client-secret",
  "subscriptionId": "your-subscription-id",
  "tenantId": "your-tenant-id",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

---

## 🔑 Method 3: Using Azure Portal

### Step 1: Create App Registration
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Name: `quantum-blue-github-actions`
4. Click "Register"
5. Note the **Application (client) ID** and **Directory (tenant) ID**

### Step 2: Create Client Secret
1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Add description: "GitHub Actions"
4. Click "Add"
5. **Copy the secret value** (you won't see it again!)

### Step 3: Assign Role
1. Go to your Resource Group in Azure Portal
2. Click "Access control (IAM)"
3. Click "Add role assignment"
4. Role: "Contributor"
5. Assign access to: "User, group, or service principal"
6. Select: "quantum-blue-github-actions"
7. Click "Save"

### Step 4: Create Credentials JSON
Use the values from Steps 1-2 to create this JSON:

```json
{
  "clientId": "your-application-client-id",
  "clientSecret": "your-client-secret-value",
  "subscriptionId": "your-subscription-id",
  "tenantId": "your-directory-tenant-id",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

---

## 📋 Add GitHub Secrets

1. Go to: https://github.com/MahendraMedapati27/Data_Management_Chatbot/settings/secrets/actions
2. Click "New repository secret"
3. Add these secrets:

   **Secret 1:**
   - Name: `AZURE_CREDENTIALS`
   - Value: (The complete JSON from above)

   **Secret 2:**
   - Name: `AZURE_RESOURCE_GROUP`
   - Value: `quantum-blue-rg` (or your resource group name)

---

## ✅ Verify Your Credentials

Your `AZURE_CREDENTIALS` JSON must contain ALL of these fields:
- ✅ `clientId` (Application ID)
- ✅ `clientSecret` (Client Secret)
- ✅ `subscriptionId` (Subscription ID)
- ✅ `tenantId` (Directory ID)
- ✅ `activeDirectoryEndpointUrl`
- ✅ `resourceManagerEndpointUrl`
- ✅ `activeDirectoryGraphResourceId`
- ✅ `sqlManagementEndpointUrl`
- ✅ `galleryEndpointUrl`
- ✅ `managementEndpointUrl`

---

## 🧪 Test Your Credentials

After adding the secrets, you can test them:

1. Go to your GitHub repository
2. Click "Actions" tab
3. Click on the latest workflow run
4. The "Login to Azure" step should now succeed

---

## 🚨 Common Issues & Solutions

### Issue: "client-id and tenant-id are missing"
**Solution**: Make sure your JSON includes both `clientId` and `tenantId` fields

### Issue: "Authentication failed"
**Solution**: Verify the `clientSecret` is correct and not expired

### Issue: "Insufficient privileges"
**Solution**: Ensure the service principal has Contributor role on the resource group

### Issue: "Resource group not found"
**Solution**: Check that `AZURE_RESOURCE_GROUP` secret matches your actual resource group name

---

## 🎯 Quick Commands Reference

```bash
# Get subscription info
az account show --query "{subscriptionId:id, tenantId:tenantId}" --output table

# List resource groups
az group list --query "[].name" --output table

# Create service principal (one-liner)
az ad sp create-for-rbac --name "quantum-blue-github-actions" --role contributor --scopes "/subscriptions/{subscription-id}/resourceGroups/{resource-group}" --sdk-auth
```

---

**🎉 Once you have the complete credentials JSON with all required fields, your GitHub Actions deployment will work perfectly!**
