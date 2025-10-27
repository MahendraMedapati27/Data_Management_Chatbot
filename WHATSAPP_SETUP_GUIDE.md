# WhatsApp Business API Setup Guide

## 📱 Complete WhatsApp Business API Integration Guide

This guide will help you set up WhatsApp Business API integration for your Quantum Blue AI Chatbot.

---

## 🔧 Step 1: Create Meta Business Account

### 1.1 Create Meta Business Account
1. Go to [business.facebook.com](https://business.facebook.com)
2. Click "Create Account"
3. Enter your business details
4. Verify your business (may require documents)

### 1.2 Create Meta Developer Account
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Sign in with your Meta Business account
3. Complete developer verification if required

---

## 🏗️ Step 2: Create WhatsApp Business App

### 2.1 Create New App
1. In Meta Developer Console, click "Create App"
2. Choose "Business" as app type
3. Enter app details:
   - App Name: "Quantum Blue Chatbot"
   - App Contact Email: your-email@domain.com
   - Business Account: Select your business account

### 2.2 Add WhatsApp Product
1. In your app dashboard, find "WhatsApp" product
2. Click "Set up" on WhatsApp
3. Choose "API Setup" (not Cloud API)

---

## 📞 Step 3: Configure Phone Number

### 3.1 Add Phone Number
1. In WhatsApp → Getting Started
2. Click "Add phone number"
3. Enter your business phone number
4. Choose verification method (SMS or Voice call)
5. Enter verification code

### 3.2 Get Credentials
After phone verification, you'll get:
- **Phone Number ID**: Found in WhatsApp → Getting Started
- **Access Token**: Click "Generate token" (temporary)

### 3.3 Create Permanent Access Token
1. Go to WhatsApp → Configuration
2. Click "Generate token"
3. Select your app
4. Choose permissions: `whatsapp_business_messaging`, `whatsapp_business_management`
5. Generate permanent token

---

## 🔗 Step 4: Configure Webhook

### 4.1 Set Webhook URL
1. In WhatsApp → Configuration
2. Webhook section:
   - **Callback URL**: `https://quantum-blue-chatbot.azurewebsites.net/webhook/whatsapp`
   - **Verify Token**: `quantum_blue_verify_token`

### 4.2 Subscribe to Fields
Subscribe to these fields:
- `messages` - For receiving messages
- `message_deliveries` - For delivery status
- `message_reads` - For read receipts

### 4.3 Test Webhook
```bash
curl -X GET "https://quantum-blue-chatbot.azurewebsites.net/webhook/whatsapp?hub.verify_token=quantum_blue_verify_token&hub.challenge=test123&hub.mode=subscribe"
```

Expected response: `test123`

---

## 📝 Step 5: Create Message Templates

### 5.1 Create Welcome Template
1. Go to WhatsApp → Message Templates
2. Click "Create Template"
3. Template details:
   - **Name**: `welcome_message`
   - **Category**: `UTILITY`
   - **Language**: `English (US)`
   - **Content**: 
     ```
     Welcome to Quantum Blue AI! 🤖
     
     I'm your AI assistant for pharmaceutical distribution services. I can help you with:
     
     • Product inquiries
     • Order placement
     • Order tracking
     • General questions
     
     How can I assist you today?
     ```

### 5.2 Create Order Confirmation Template
1. Create another template:
   - **Name**: `order_confirmation`
   - **Category**: `UTILITY`
   - **Language**: `English (US)`
   - **Content**:
     ```
     Order Confirmation ✅
     
     Order ID: {{1}}
     Amount: ₹{{2}}
     Status: {{3}}
     
     Thank you for your order! We'll process it shortly.
     ```

---

## 🔧 Step 6: Configure Azure App Service

### 6.1 Set Environment Variables
In Azure Portal → App Service → Configuration → Application settings:

```
WHATSAPP_ACCESS_TOKEN = your-permanent-access-token
WHATSAPP_PHONE_NUMBER_ID = your-phone-number-id
WHATSAPP_VERIFY_TOKEN = quantum_blue_verify_token
WHATSAPP_WEBHOOK_URL = https://quantum-blue-chatbot.azurewebsites.net/webhook/whatsapp
WHATSAPP_API_VERSION = v22.0
```

### 6.2 Test Configuration
```bash
# Test webhook verification
curl -X GET "https://quantum-blue-chatbot.azurewebsites.net/webhook/whatsapp?hub.verify_token=quantum_blue_verify_token&hub.challenge=test&hub.mode=subscribe"

# Test sending message (replace with your number)
curl -X POST "https://quantum-blue-chatbot.azurewebsites.net/webhook/send-message" \
  -H "Content-Type: application/json" \
  -d '{"to": "1234567890", "message": "Hello from Quantum Blue!"}'
```

---

## 🧪 Step 7: Testing WhatsApp Integration

### 7.1 Test Message Flow
1. Send a message to your WhatsApp Business number
2. Check Azure logs for webhook activity
3. Verify the bot responds correctly

### 7.2 Test Different Message Types
- Text messages
- Order requests
- Product inquiries
- General questions

### 7.3 Monitor Webhook Logs
```bash
az webapp log tail --name quantum-blue-chatbot --resource-group quantum-blue-rg
```

---

## 🔒 Step 8: Security and Best Practices

### 8.1 Webhook Security
- Always validate webhook signatures
- Use HTTPS for webhook URL
- Implement rate limiting
- Log all webhook activity

### 8.2 Message Handling
- Validate incoming message format
- Handle different message types
- Implement error handling
- Set up message queuing for high volume

### 8.3 User Privacy
- Comply with WhatsApp Business Policy
- Implement opt-in/opt-out functionality
- Handle user data securely
- Provide clear privacy notices

---

## 📊 Step 9: Monitoring and Analytics

### 9.1 WhatsApp Analytics
1. Go to WhatsApp → Analytics
2. Monitor:
   - Message delivery rates
   - Response times
   - User engagement
   - Error rates

### 9.2 Azure Monitoring
1. Enable Application Insights
2. Set up alerts for:
   - Webhook failures
   - High error rates
   - Performance issues

### 9.3 Custom Metrics
Track these metrics:
- Messages received per hour
- Response success rate
- Average response time
- User satisfaction scores

---

## 🚨 Troubleshooting Common Issues

### Issue: Webhook not receiving messages
**Solutions**:
- Check webhook URL is accessible
- Verify webhook subscription
- Check Azure app service logs
- Ensure verify token matches

### Issue: Messages not sending
**Solutions**:
- Verify access token is valid
- Check phone number ID
- Ensure message format is correct
- Check rate limits

### Issue: Template messages failing
**Solutions**:
- Verify template is approved
- Check template parameters
- Ensure template is in correct language
- Check template usage limits

### Issue: High latency
**Solutions**:
- Optimize database queries
- Use caching for frequent responses
- Implement message queuing
- Scale Azure app service

---

## 📈 Step 10: Advanced Features

### 10.1 Interactive Messages
Implement buttons and quick replies:
```python
# Example interactive message
buttons = [
    {"type": "reply", "reply": {"id": "products", "title": "View Products"}},
    {"type": "reply", "reply": {"id": "orders", "title": "My Orders"}},
    {"type": "reply", "reply": {"id": "help", "title": "Help"}}
]
```

### 10.2 Media Messages
Handle images, documents, and voice messages:
```python
# Handle different media types
if message_type == 'image':
    # Process image
elif message_type == 'document':
    # Process document
elif message_type == 'audio':
    # Process voice message
```

### 10.3 Location Sharing
Handle location messages for delivery:
```python
# Process location message
if message_type == 'location':
    latitude = message['location']['latitude']
    longitude = message['location']['longitude']
    # Use for delivery calculations
```

---

## 📚 Additional Resources

- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp/)
- [WhatsApp Business Policy](https://www.whatsapp.com/business/api/policy/)
- [Meta Business Help Center](https://www.facebook.com/business/help)
- [WhatsApp Business API Pricing](https://developers.facebook.com/docs/whatsapp/pricing)

---

## 🎯 Next Steps

1. **Message Templates**: Create more templates for different scenarios
2. **Analytics**: Set up comprehensive analytics dashboard
3. **Automation**: Implement automated responses for common queries
4. **Integration**: Connect with CRM and order management systems
5. **Scaling**: Implement message queuing for high volume

---

**🎉 Congratulations!** Your WhatsApp Business API integration is now complete!
