# 🚀 QUANTUM BLUE AI CHATBOT - SETUP & RUN GUIDE

## 📋 Project Analysis Summary

This is a **Flask-based AI chatbot application** with the following features:

### 🏗️ **Architecture**
- **Flask App Factory Pattern** with blueprints
- **Modular Design**: Auth, Chatbot, WhatsApp webhook modules
- **Database Support**: SQL Server (Azure) with SQLite fallback
- **AI Integration**: Groq LLM service (replacing Azure OpenAI)
- **Authentication**: Email-based OTP verification
- **WhatsApp Integration**: Business API webhook support

### 📁 **Key Files Structure**
```
chatbot-project/
├── app/                    # Flask application modules
│   ├── __init__.py        # App factory & configuration
│   ├── auth.py            # Authentication routes
│   ├── chatbot.py         # Main chat functionality
│   ├── whatsapp_webhook.py # WhatsApp integration
│   ├── groq_service.py    # AI service (Groq)
│   ├── models.py          # Database models
│   └── ...                # Other services
├── static/                # CSS, JS assets
├── templates/             # HTML templates
├── config.py              # Configuration management
├── run.py                 # ✅ NEW: Application entry point
├── start_chatbot.bat      # ✅ NEW: Windows batch script
├── start_chatbot.ps1      # ✅ NEW: PowerShell script
└── requirements.txt       # Python dependencies
```

## 🛠️ **Setup Instructions**

### 1. **Prerequisites**
- ✅ **Anaconda/Miniconda** installed
- ✅ **Python 3.9+** (recommended)
- ✅ **Git** (for version control)

### 2. **Environment Setup**

#### **Option A: Using Conda (Recommended)**
```bash
# Create conda environment
conda create -n highvolt python=3.9

# Activate environment
conda activate highvolt

# Install dependencies
pip install -r requirements.txt
```

#### **Option B: Using Virtual Environment**
```bash
# Create virtual environment
python -m venv highvolt_env

# Activate (Windows)
highvolt_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. **Configuration Setup**

#### **Create Environment File**
Copy the example configuration:
```bash
# Copy the example (if available)
copy .env.example .env

# Or create manually
notepad .env
```

#### **Required Environment Variables**
```env
# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production-12345
SECURITY_PASSWORD_SALT=your-security-salt-change-in-production-67890

# Flask Development Settings
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# AI Service (Groq)
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=mixtral-8x7b-32768

# Email Service (for OTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

#### **Optional Services**
- **WhatsApp Integration**: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`
- **Web Search**: `TAVILY_API_KEY`
- **Database**: `SQL_SERVER`, `SQL_DATABASE`, `SQL_USERNAME`, `SQL_PASSWORD`
- **Azure Storage**: `AZURE_STORAGE_CONNECTION_STRING`

## 🚀 **Running the Application**

### **Method 1: Direct Python (Recommended)**
```bash
# Activate conda environment
conda activate highvolt

# Navigate to project directory
cd "D:\High Volt\new2\chatbot-project"

# Run the application
python run.py
```

### **Method 2: Windows Batch Script**
```bash
# Double-click or run from command line
start_chatbot.bat
```

### **Method 3: PowerShell Script**
```powershell
# Run from PowerShell
.\start_chatbot.ps1
```

## 🌐 **Access the Application**

Once running, the chatbot will be available at:
- **Local**: http://localhost:5000
- **Network**: http://0.0.0.0:5000 (if FLASK_HOST=0.0.0.0)

## 🔧 **Service Status Check**

The application will show service status on startup:
```
🔧 Service Status:
   Groq AI Service: ✅ Available / ❌ Not configured
   Email Service (OTP): ✅ Available / ❌ Not configured
   WhatsApp Integration: ✅ Available / ❌ Not configured
   Web Search Service: ✅ Available / ❌ Not configured
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Import Errors**
   ```bash
   # Solution: Install missing dependencies
   pip install -r requirements.txt
   ```

2. **Database Connection Issues**
   ```bash
   # The app will fallback to SQLite automatically
   # Check your SQL Server configuration in .env
   ```

3. **Email Not Sending**
   ```bash
   # Check SMTP settings in .env
   # Use app passwords for Gmail
   ```

4. **Conda Environment Issues**
   ```bash
   # Recreate environment
   conda remove -n highvolt --all
   conda create -n highvolt python=3.9
   conda activate highvolt
   pip install -r requirements.txt
   ```

### **Development Mode**
```env
# Enable debug mode
FLASK_DEBUG=True
FLASK_ENV=development
```

### **Production Mode**
```env
# Disable debug mode
FLASK_DEBUG=False
FLASK_ENV=production
SECRET_KEY=strong-production-secret-key
```

## 📱 **Features Available**

### **Core Features**
- ✅ **AI Chat Interface** (Groq-powered)
- ✅ **User Authentication** (Email + OTP)
- ✅ **Conversation History**
- ✅ **Responsive Web UI**
- ✅ **WhatsApp Integration** (if configured)
- ✅ **Web Search** (if configured)

### **Demo Mode**
The application works in **demo mode** without full configuration:
- Uses fallback responses for common queries
- Loads local sample data
- Full UI functionality
- Basic authentication

## 🔐 **Security Notes**

1. **Change Default Secrets**: Update `SECRET_KEY` and `SECURITY_PASSWORD_SALT`
2. **Environment Variables**: Never commit `.env` file to version control
3. **Production**: Use strong passwords and HTTPS
4. **Database**: Use connection pooling and proper authentication

## 📞 **Support**

If you encounter issues:
1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check network connectivity for external services

---

## 🎯 **Quick Start Commands**

```bash
# 1. Setup environment
conda create -n highvolt python=3.9
conda activate highvolt

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# Edit .env file with your settings

# 4. Run application
python run.py

# 5. Access chatbot
# Open browser to http://localhost:5000
```

**🎉 Your Quantum Blue AI Chatbot is now ready to run!**
