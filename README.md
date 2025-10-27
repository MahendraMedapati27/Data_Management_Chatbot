# 🤖 Quantum Blue AI Chatbot

A sophisticated AI-powered chatbot for pharmaceutical distribution services with WhatsApp Business API integration, deployed on Azure App Service.

## 🌟 Features

- **AI-Powered Conversations**: Powered by Groq's high-speed LLM models
- **WhatsApp Integration**: Full WhatsApp Business API support
- **Order Management**: Complete order placement and tracking system
- **Product Catalog**: Dynamic product inquiry and management
- **Multi-Platform**: Web interface and WhatsApp messaging
- **Azure Deployment**: Production-ready Azure App Service deployment
- **Database Integration**: Azure SQL Database with SQLite fallback
- **Email Services**: OTP verification and notifications
- **Web Search**: Integrated web search capabilities

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Azure Account
- WhatsApp Business API Account
- Groq API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MahendraMedapati27/Data_Management_Chatbot.git
   cd Data_Management_Chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp azure_config.env .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

## ☁️ Azure Deployment

### Automated Deployment

1. **Fork this repository**
2. **Create Azure App Service**
3. **Configure GitHub deployment**
4. **Set environment variables**
5. **Deploy**

For detailed deployment instructions, see [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)

### Manual Deployment

```bash
# Create resource group
az group create --name "quantum-blue-rg" --location "East US"

# Create app service plan
az appservice plan create --name "quantum-blue-plan" --resource-group "quantum-blue-rg" --sku "B1" --is-linux

# Create web app
az webapp create --resource-group "quantum-blue-rg" --plan "quantum-blue-plan" --name "quantum-blue-chatbot" --runtime "PYTHON|3.9"

# Configure GitHub deployment
az webapp deployment source config --resource-group "quantum-blue-rg" --name "quantum-blue-chatbot" --repo-url "https://github.com/MahendraMedapati27/Data_Management_Chatbot.git" --branch main --manual-integration
```

## 📱 WhatsApp Integration

### Setup WhatsApp Business API

1. **Create Meta Business Account**
2. **Set up WhatsApp Business API**
3. **Configure webhook**
4. **Create message templates**

For detailed WhatsApp setup, see [WHATSAPP_SETUP_GUIDE.md](WHATSAPP_SETUP_GUIDE.md)

### Webhook Configuration

- **Webhook URL**: `https://your-app.azurewebsites.net/webhook/whatsapp`
- **Verify Token**: `quantum_blue_verify_token`
- **Subscribed Fields**: `messages`, `message_deliveries`, `message_reads`

## 🔧 Configuration

### Required Environment Variables

```bash
# Core Flask Settings
FLASK_ENV=production
SECRET_KEY=your-secret-key
SECURITY_PASSWORD_SALT=your-salt

# AI Service
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=mixtral-8x7b-32768

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_VERIFY_TOKEN=quantum_blue_verify_token
WHATSAPP_WEBHOOK_URL=https://your-app.azurewebsites.net/webhook/whatsapp

# Database (Optional - uses SQLite if not provided)
SQL_SERVER=your-sql-server.database.windows.net
SQL_DATABASE=your-database
SQL_USERNAME=your-username
SQL_PASSWORD=your-password

# Email Service
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=your-email@gmail.com

# Web Search (Optional)
TAVILY_API_KEY=your-tavily-api-key
```

### Azure App Service Configuration

Set these in Azure Portal → App Service → Configuration → Application settings:

```
FLASK_ENV = production
FLASK_DEBUG = false
FLASK_HOST = 0.0.0.0
FLASK_PORT = 8000
PYTHONUNBUFFERED = 1
WEBSITE_PYTHON_DEFAULT_VERSION = 3.9
SECRET_KEY = your-production-secret-key
GROQ_API_KEY = your-groq-api-key
WHATSAPP_ACCESS_TOKEN = your-whatsapp-access-token
WHATSAPP_PHONE_NUMBER_ID = your-phone-number-id
WHATSAPP_VERIFY_TOKEN = quantum_blue_verify_token
WHATSAPP_WEBHOOK_URL = https://your-app.azurewebsites.net/webhook/whatsapp
```

## 📊 API Endpoints

### Web Interface
- `GET /` - Main chat interface
- `GET /chat` - Chat page
- `POST /chat/send` - Send message
- `GET /health` - Health check

### WhatsApp Webhook
- `GET /webhook/whatsapp` - Webhook verification
- `POST /webhook/whatsapp` - Receive messages
- `POST /webhook/send-message` - Send message
- `POST /webhook/send-template` - Send template

### Authentication
- `GET /auth/login` - Login page
- `POST /auth/login` - Login
- `GET /auth/verify-otp` - OTP verification
- `POST /auth/verify-otp` - Verify OTP

## 🏗️ Project Structure

```
chatbot-project/
├── app/                          # Flask application
│   ├── __init__.py              # App factory
│   ├── auth.py                  # Authentication routes
│   ├── chatbot.py               # Chat interface
│   ├── whatsapp_webhook.py      # WhatsApp integration
│   ├── whatsapp_service.py      # WhatsApp API service
│   ├── groq_service.py          # AI service
│   ├── models.py                # Database models
│   └── ...                      # Other services
├── templates/                   # HTML templates
├── static/                      # CSS/JS assets
├── run.py                       # Development server
├── startup.py                   # Azure production server
├── web.config                   # Azure IIS configuration
├── requirements.txt             # Python dependencies
├── azure_config.env            # Azure configuration template
├── AZURE_DEPLOYMENT_GUIDE.md   # Deployment guide
├── WHATSAPP_SETUP_GUIDE.md     # WhatsApp setup guide
└── README.md                    # This file
```

## 🔍 Monitoring and Logs

### Azure Logs
```bash
# View real-time logs
az webapp log tail --name quantum-blue-chatbot --resource-group quantum-blue-rg

# Download logs
az webapp log download --name quantum-blue-chatbot --resource-group quantum-blue-rg
```

### Health Check
- **Endpoint**: `/health`
- **Response**: `{"status": "healthy", "service": "quantum-blue-chatbot"}`

### WhatsApp Webhook Testing
```bash
curl -X GET "https://your-app.azurewebsites.net/webhook/whatsapp?hub.verify_token=quantum_blue_verify_token&hub.challenge=test&hub.mode=subscribe"
```

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=true

# Run development server
python run.py
```

### Testing WhatsApp Integration
```bash
# Test webhook
curl -X POST "https://your-app.azurewebsites.net/webhook/send-message" \
  -H "Content-Type: application/json" \
  -d '{"to": "1234567890", "message": "Hello from Quantum Blue!"}'
```

## 🔒 Security

### Best Practices
- Use strong, unique secret keys
- Enable HTTPS (automatic in Azure)
- Validate webhook signatures
- Implement rate limiting
- Regular security updates
- Monitor for suspicious activity

### Environment Security
- Never commit API keys to Git
- Use Azure Key Vault for sensitive data
- Rotate credentials regularly
- Enable Azure Security Center

## 📈 Performance Optimization

### Azure Optimizations
- Use appropriate App Service Plan
- Enable Application Insights
- Configure auto-scaling
- Use Azure CDN for static files
- Implement caching strategies

### Database Optimizations
- Use connection pooling
- Optimize queries
- Implement proper indexing
- Regular maintenance

## 🆘 Troubleshooting

### Common Issues

#### App won't start
- Check Python version (3.9)
- Verify requirements.txt
- Check environment variables
- Review Azure logs

#### Database connection fails
- Verify connection string
- Check firewall rules
- Ensure database exists
- Test connection manually

#### WhatsApp webhook not working
- Verify webhook URL
- Check verify token
- Ensure HTTPS
- Review webhook logs

#### High latency
- Check database performance
- Optimize queries
- Scale App Service Plan
- Implement caching

### Debug Commands
```bash
# Check app status
az webapp show --name quantum-blue-chatbot --resource-group quantum-blue-rg

# Restart app
az webapp restart --name quantum-blue-chatbot --resource-group quantum-blue-rg

# View configuration
az webapp config appsettings list --name quantum-blue-chatbot --resource-group quantum-blue-rg
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

- **Documentation**: See the guides in this repository
- **Issues**: Create GitHub issues for bugs and feature requests
- **Azure Support**: Use Azure support channels for infrastructure issues
- **WhatsApp Support**: Contact Meta Business Support for API issues

## 🎯 Roadmap

- [ ] Enhanced analytics dashboard
- [ ] Multi-language support
- [ ] Advanced order management
- [ ] Integration with CRM systems
- [ ] Voice message support
- [ ] Advanced AI features
- [ ] Mobile app integration

---

**🚀 Ready to deploy?** Follow the [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md) to get started!

**📱 Want WhatsApp integration?** Check out the [WhatsApp Setup Guide](WHATSAPP_SETUP_GUIDE.md)!#   D e p l o y m e n t   T e s t   -   1 0 / 2 7 / 2 0 2 5   1 4 : 1 3 : 4 3  
 