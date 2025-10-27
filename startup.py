#!/usr/bin/env python3
"""
Azure App Service Startup Script
This script is specifically designed for Azure App Service deployment
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set Azure-specific environment variables
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', 'false')
os.environ.setdefault('FLASK_HOST', '0.0.0.0')
os.environ.setdefault('FLASK_PORT', '8000')

def main():
    """Azure App Service entry point"""
    try:
        # Import and create the Flask app
        from app import create_app
        
        # Create the Flask application instance
        app = create_app()
        
        # Get configuration from environment
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 8000))
        
        print("=" * 60)
        print("🚀 QUANTUM BLUE AI CHATBOT - AZURE DEPLOYMENT")
        print("=" * 60)
        print(f"📡 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"🌐 Environment: {os.getenv('FLASK_ENV', 'production')}")
        print(f"☁️  Azure App Service: {os.getenv('WEBSITE_SITE_NAME', 'Unknown')}")
        print("=" * 60)
        
        # Check for required environment variables
        required_vars = ['SECRET_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print("⚠️  WARNING: Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\n💡 Set these in Azure App Service Configuration.")
            print()
        
        # Check for optional but important services
        optional_services = {
            'GROQ_API_KEY': 'Groq AI Service',
            'MAIL_USERNAME': 'Email Service (OTP)',
            'WHATSAPP_ACCESS_TOKEN': 'WhatsApp Integration',
            'TAVILY_API_KEY': 'Web Search Service'
        }
        
        print("🔧 Service Status:")
        for env_var, service_name in optional_services.items():
            status = "✅ Available" if os.getenv(env_var) else "❌ Not configured"
            print(f"   {service_name}: {status}")
        
        print("=" * 60)
        print("🌐 Starting Azure App Service...")
        print(f"📱 Webhook URL: https://{os.getenv('WEBSITE_SITE_NAME', 'your-app')}.azurewebsites.net/webhook/whatsapp")
        print("=" * 60)
        
        # Use waitress for production deployment
        from waitress import serve
        serve(app, host=host, port=port, threads=4)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all dependencies are installed.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Application Error: {e}")
        print("💡 Check your Azure App Service configuration.")
        sys.exit(1)

if __name__ == '__main__':
    main()
