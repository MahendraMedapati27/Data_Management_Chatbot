# Quantum Blue AI Chatbot - Azure Deployment Guide

## 🚀 Complete Deployment Guide for Azure App Service with WhatsApp Integration

This guide will help you deploy your Quantum Blue AI Chatbot to Azure App Service and connect it with WhatsApp Business API.

---

## 📋 Prerequisites

### Required Accounts & Services
1. **Azure Account** with active subscription
2. **GitHub Account** 
3. **WhatsApp Business API Account** (via Meta Business)
4. **Groq API Account** (for AI services)
5. **Azure SQL Database** (optional, can use SQLite)

### Required API Keys & Credentials
- Groq API Key
- WhatsApp Business API Access Token
- WhatsApp Phone Number ID
- Azure SQL Database connection string (if using)
- Email SMTP credentials (for OTP)

---

## 🔧 Step 1: Prepare Your Code for GitHub

### 1.1 Initialize Git Repository
```bash
cd "D:\High Volt\new2\chatbot-project"
git init
git add .
git commit -m "Initial commit: Quantum Blue AI Chatbot"
```

### 1.2 Connect to GitHub Repository
```bash
git remote add origin https://github.com/MahendraMedapati27/Data_Management_Chatbot.git
git branch -M main
git push -u origin main
```

---

## ☁️ Step 2: Create Azure Resources

### 2.1 Create Resource Group
```bash
az group create --name "quantum-blue-rg" --location "East US"
```

### 2.2 Create App Service Plan
```bash
az appservice plan create --name "quantum-blue-plan" --resource-group "quantum-blue-rg" --sku "B1" --is-linux
```

### 2.3 Create Web App
```bash
az webapp create --resource-group "quantum-blue-rg" --plan "quantum-blue-plan" --name "quantum-blue-chatbot" --runtime "PYTHON|3.9"
```

### 2.4 Create Azure SQL Database (Optional)
```bash
az sql server create --name "quantum-blue-sql" --resource-group "quantum-blue-rg" --location "East US" --admin-user "quantumadmin" --admin-password "YourSecurePassword123!"
az sql db create --resource-group "quantum-blue-rg" --server "quantum-blue-sql" --name "quantumbotdb" --service-objective "S0"
```

---

## ⚙️ Step 3: Configure Azure App Service

### 3.1 Set Application Settings
Go to Azure Portal → App Services → quantum-blue-chatbot → Configuration → Application settings

Add these settings:

#### Core Flask Settings
```
FLASK_ENV = production
FLASK_DEBUG = false
FLASK_HOST = 0.0.0.0
FLASK_PORT = 8000
PYTHONUNBUFFERED = 1
WEBSITE_PYTHON_DEFAULT_VERSION = 3.9
```

#### Security Settings (CHANGE THESE!)
```
SECRET_KEY = your-unique-secret-key-here
SECURITY_PASSWORD_SALT = your-unique-salt-here
```

#### Groq AI Configuration
```
GROQ_API_KEY = your-groq-api-key
GROQ_MODEL = mixtral-8x7b-32768
```

#### WhatsApp Business API Configuration
```
WHATSAPP_ACCESS_TOKEN = your-whatsapp-access-token
WHATSAPP_PHONE_NUMBER_ID = your-phone-number-id
WHATSAPP_VERIFY_TOKEN = quantum_blue_verify_token
WHATSAPP_WEBHOOK_URL = https://quantum-blue-chatbot.azurewebsites.net/webhook/whatsapp
WHATSAPP_API_VERSION = v22.0
```

#### Database Configuration (if using Azure SQL)
```
SQL_SERVER = quantum-blue-sql.database.windows.net
SQL_DATABASE = quantumbotdb
SQL_USERNAME = quantumadmin
SQL_PASSWORD = YourSecurePassword123!
REQUIRE_AZURE_DB = true
```

#### Email Configuration
```
MAIL_SERVER = smtp.gmail.com
MAIL_PORT = 587
MAIL_USE_TLS = true
MAIL_USERNAME = your-email@gmail.com
MAIL_PASSWORD = your-app-password
ADMIN_EMAIL = your-email@gmail.com
```

#### Web Search API (Optional)
```
TAVILY_API_KEY = your-tavily-api-key
```

### 3.2 Configure GitHub Deployment
```bash
az webapp deployment source config --resource-group "quantum-blue-rg" --name "quantum-blue-chatbot" --repo-url "https://github.com/MahendraMedapati27/Data_Management_Chatbot.git" --branch main --manual-integration
```

---

## 📱 Step 4: Configure WhatsApp Business API

### 4.1 Set Up WhatsApp Business Account
1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app
3. Add WhatsApp Business API product
4. Get your access token and phone number ID

### 4.2 Configure Webhook
1. In Meta Developer Console, go to WhatsApp → Configuration
2. Set webhook URL: `https://quantum-blue-chatbot.azurewebsites.net/webhook/whatsapp`
3. Set verify token: `quantum_blue_verify_token`
4. Subscribe to `messages` field

### 4.3 Test Webhook
```bash
curl -X GET "https://quantum-blue-chatbot.azurewebsites.net/webhook/whatsapp?hub.verify_token=quantum_blue_verify_token&hub.challenge=test&hub.mode=subscribe"
```

---

## 🚀 Step 5: Deploy and Test

### 5.1 Deploy from GitHub
1. Go to Azure Portal → App Services → quantum-blue-chatbot
2. Go to Deployment Center
3. Connect to GitHub repository
4. Select branch: `main`
5. Deploy

### 5.2 Test the Application
1. Visit: `https://quantum-blue-chatbot.azurewebsites.net`
2. Test chatbot functionality
3. Test WhatsApp webhook: `https://quantum-blue-chatbot.azurewebsites.net/health`

### 5.3 Test WhatsApp Integration
1. Send a message to your WhatsApp Business number
2. Check Azure logs for webhook activity
3. Verify responses are sent back

---

## 🔍 Step 6: Monitoring and Troubleshooting

### 6.1 Enable Logging
```bash
az webapp log config --resource-group "quantum-blue-rg" --name "quantum-blue-chatbot" --application-logging true --level information
```

### 6.2 View Logs
```bash
az webapp log tail --resource-group "quantum-blue-rg" --name "quantum-blue-chatbot"
```

### 6.3 Common Issues & Solutions

#### Issue: App won't start
**Solution**: Check Python version and requirements.txt

#### Issue: Database connection fails
**Solution**: Verify SQL connection string and firewall rules

#### Issue: WhatsApp webhook not receiving messages
**Solution**: Check webhook URL and verify token

#### Issue: Environment variables not loading
**Solution**: Restart the app service after setting variables

---

## 📊 Step 7: Production Optimization

### 7.1 Enable HTTPS
- Azure App Service provides HTTPS by default
- Custom domain can be added in Custom domains section

### 7.2 Set Up Monitoring
1. Enable Application Insights
2. Set up alerts for errors
3. Monitor performance metrics

### 7.3 Scale Configuration
- Upgrade to higher App Service Plan for better performance
- Configure auto-scaling rules

---

## 🔐 Security Best Practices

### 7.1 Environment Variables
- Never commit API keys to GitHub
- Use Azure Key Vault for sensitive data
- Rotate keys regularly

### 7.2 Database Security
- Enable SSL for database connections
- Use managed identity when possible
- Regular security updates

### 7.3 WhatsApp Security
- Validate webhook signatures
- Implement rate limiting
- Monitor for suspicious activity

---

## 📞 Support and Maintenance

### Monitoring Endpoints
- Health Check: `/health`
- WhatsApp Webhook: `/webhook/whatsapp`
- Chat Interface: `/chat`

### Regular Maintenance Tasks
1. Update dependencies monthly
2. Monitor API usage and costs
3. Review and rotate credentials
4. Backup database regularly
5. Monitor application performance

---

## 🎯 Next Steps

1. **Custom Domain**: Add your custom domain
2. **SSL Certificate**: Configure custom SSL
3. **CDN**: Add Azure CDN for static files
4. **Backup**: Set up automated backups
5. **Monitoring**: Configure advanced monitoring

---

## 📚 Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp/)
- [Groq API Documentation](https://console.groq.com/docs)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.0.x/deploying/)

---

## 🆘 Troubleshooting Commands

```bash
# Check app status
az webapp show --name quantum-blue-chatbot --resource-group quantum-blue-rg

# Restart app
az webapp restart --name quantum-blue-chatbot --resource-group quantum-blue-rg

# View logs
az webapp log tail --name quantum-blue-chatbot --resource-group quantum-blue-rg

# Update app settings
az webapp config appsettings set --name quantum-blue-chatbot --resource-group quantum-blue-rg --settings KEY=VALUE
```

---

**🎉 Congratulations!** Your Quantum Blue AI Chatbot is now deployed on Azure and connected to WhatsApp!
