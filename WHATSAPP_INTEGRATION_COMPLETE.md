# 🎉 WhatsApp Integration Setup Guide

## ✅ **Your App is Successfully Deployed!**

Your chatbot is now running at: **https://my-chatbot-app-73d666.azurewebsites.net**

## 📱 **WhatsApp Configuration Details**

### **Webhook URL:**
```
https://my-chatbot-app-73d666.azurewebsites.net/webhook/whatsapp
```

### **Verify Token:**
```
quantum_blue_verify_token
```

---

## 🔧 **Step 1: Set Up WhatsApp Business API**

### **1.1 Create Meta Business Account**
1. Go to [business.facebook.com](https://business.facebook.com)
2. Create a business account
3. Verify your business (may require documents)

### **1.2 Create Meta Developer Account**
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Sign in with your Meta Business account
3. Create a new app → Choose "Business"

### **1.3 Add WhatsApp Product**
1. In your app dashboard, find "WhatsApp" product
2. Click "Set up" on WhatsApp
3. Choose "API Setup"

### **1.4 Configure Phone Number**
1. Add your business phone number
2. Verify via SMS or Voice call
3. Note down your **Phone Number ID**

### **1.5 Get Access Token**
1. Go to WhatsApp → Getting Started
2. Click "Generate token"
3. Copy your **Access Token**

---

## ⚙️ **Step 2: Configure Azure App Service**

### **2.1 Go to Azure Portal**
1. Navigate to: https://portal.azure.com
2. Go to **App Services** → **my-chatbot-app-73d666**
3. Click **Configuration** → **Application settings**

### **2.2 Add Required Settings**

Click **"+ New application setting"** for each:

#### **Core Settings:**
```
Name: SECRET_KEY
Value: your-unique-secret-key-change-this

Name: GROQ_API_KEY
Value: your-groq-api-key

Name: WHATSAPP_ACCESS_TOKEN
Value: your-whatsapp-access-token

Name: WHATSAPP_PHONE_NUMBER_ID
Value: your-phone-number-id

Name: WHATSAPP_VERIFY_TOKEN
Value: quantum_blue_verify_token

Name: WHATSAPP_WEBHOOK_URL
Value: https://my-chatbot-app-73d666.azurewebsites.net/webhook/whatsapp
```

#### **Optional Settings:**
```
Name: MAIL_USERNAME
Value: your-email@gmail.com

Name: MAIL_PASSWORD
Value: your-app-password

Name: TAVILY_API_KEY
Value: your-tavily-api-key
```

### **2.3 Save and Restart**
1. Click **Save**
2. Go to **Overview** → **Restart**

---

## 🔗 **Step 3: Configure WhatsApp Webhook**

### **3.1 Set Up Webhook in Meta Developer Console**
1. Go to your WhatsApp app in Meta Developer Console
2. Navigate to **WhatsApp** → **Configuration**
3. **Webhook section**:
   - **Callback URL**: `https://my-chatbot-app-73d666.azurewebsites.net/webhook/whatsapp`
   - **Verify Token**: `quantum_blue_verify_token`
4. Click **Verify and Save**

### **3.2 Subscribe to Fields**
Subscribe to these fields:
- ✅ `messages` - For receiving messages
- ✅ `message_deliveries` - For delivery status
- ✅ `message_reads` - For read receipts

---

## 🧪 **Step 4: Test Your Setup**

### **4.1 Test Webhook Verification**
Visit this URL in your browser:
```
https://my-chatbot-app-73d666.azurewebsites.net/webhook/whatsapp?hub.verify_token=quantum_blue_verify_token&hub.challenge=test123&hub.mode=subscribe
```

**Expected response**: `test123`

### **4.2 Test Health Endpoint**
Visit: `https://my-chatbot-app-73d666.azurewebsites.net/health`

**Expected response**: `{"status": "healthy", "service": "quantum-blue-chatbot"}`

### **4.3 Test Web Interface**
Visit: `https://my-chatbot-app-73d666.azurewebsites.net`

### **4.4 Test WhatsApp Integration**
1. Send a message to your WhatsApp Business number
2. Check Azure logs for webhook activity
3. Verify the bot responds

---

## 📊 **Step 5: Monitor Your Chatbot**

### **5.1 Azure Logs**
```bash
# View real-time logs
az webapp log tail --name my-chatbot-app-73d666 --resource-group chatbot-rg
```

### **5.2 GitHub Actions**
- Monitor deployments in the **Actions** tab
- Check for any failed deployments

### **5.3 WhatsApp Analytics**
- Go to Meta Developer Console → WhatsApp → Analytics
- Monitor message delivery and response rates

---

## 🚨 **Troubleshooting**

### **Issue: Webhook verification fails**
**Solution**: 
- Check that `WHATSAPP_VERIFY_TOKEN` is set to `quantum_blue_verify_token`
- Ensure the webhook URL is accessible
- Check Azure App Service logs

### **Issue: Messages not received**
**Solution**:
- Verify `WHATSAPP_ACCESS_TOKEN` is correct
- Check `WHATSAPP_PHONE_NUMBER_ID` is correct
- Ensure webhook is subscribed to `messages` field

### **Issue: Bot doesn't respond**
**Solution**:
- Check `GROQ_API_KEY` is set
- Verify all environment variables are saved
- Restart the Azure App Service

### **Issue: App won't start**
**Solution**:
- Check Azure logs for errors
- Verify all required environment variables are set
- Check Python dependencies in requirements.txt

---

## 🎯 **Quick Reference**

### **Your App URLs:**
- **Main App**: https://my-chatbot-app-73d666.azurewebsites.net
- **Health Check**: https://my-chatbot-app-73d666.azurewebsites.net/health
- **WhatsApp Webhook**: https://my-chatbot-app-73d666.azurewebsites.net/webhook/whatsapp

### **WhatsApp Configuration:**
- **Webhook URL**: `https://my-chatbot-app-73d666.azurewebsites.net/webhook/whatsapp`
- **Verify Token**: `quantum_blue_verify_token`
- **Required Fields**: `messages`, `message_deliveries`, `message_reads`

### **Required Environment Variables:**
- `SECRET_KEY`
- `GROQ_API_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_VERIFY_TOKEN`
- `WHATSAPP_WEBHOOK_URL`

---

## 🎉 **You're All Set!**

Once you complete these steps:
1. ✅ Your chatbot will be accessible via WhatsApp
2. ✅ Users can send messages to your WhatsApp Business number
3. ✅ The bot will respond automatically
4. ✅ All conversations will be logged in Azure

**🚀 Start by setting up the WhatsApp Business API and configuring the environment variables in Azure Portal!**
