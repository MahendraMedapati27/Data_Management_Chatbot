import logging
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail, db
from app.models import EmailLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(to_email, subject, html_content, email_type='general'):
    """Send email via SMTP"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=html_content,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        
        # Log successful email in a separate transaction
        try:
            # Ensure we have a clean transaction state
            db.session.rollback()  # Clear any existing transaction
            email_log = EmailLog(
                recipient=to_email,
                email_type=email_type,
                status='sent'
            )
            db.session.add(email_log)
            db.session.commit()
        except Exception as log_e:
            logger.warning(f'Failed to log email success: {str(log_e)}')
            # Don't fail the email send if logging fails
            try:
                db.session.rollback()
            except:
                pass
        
        logger.info(f'Email sent to {to_email}')
        return True
        
    except Exception as e:
        logger.error(f'Email sending failed: {str(e)}')
        
        # Log failure in a separate transaction
        try:
            # Ensure we have a clean transaction state
            db.session.rollback()  # Clear any existing transaction
            email_log = EmailLog(
                recipient=to_email,
                email_type=email_type,
                status='failed',
                error_message=str(e)
            )
            db.session.add(email_log)
            db.session.commit()
        except Exception as log_e:
            logger.warning(f'Failed to log email failure: {str(log_e)}')
            # Don't fail if logging fails
            try:
                db.session.rollback()
            except:
                pass
        
        return False

def send_otp_email(user_email, user_name, otp):
    """Send OTP verification email"""
    subject = 'Email Verification - Your OTP Code'
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background-color: #f9f9f9;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                color: #007bff;
                margin-bottom: 30px;
            }}
            .otp-box {{
                background-color: #007bff;
                color: white;
                font-size: 32px;
                font-weight: bold;
                text-align: center;
                padding: 20px;
                border-radius: 8px;
                letter-spacing: 8px;
                margin: 30px 0;
            }}
            .info {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                color: #666;
                font-size: 14px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }}
            .button {{
                display: inline-block;
                background-color: #28a745;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Welcome to Quantum Blue!</h1>
            </div>
            
            <p>Hello <strong>{user_name}</strong>,</p>
            
            <p>Thank you for registering! To complete your registration, please use the following One-Time Password (OTP):</p>
            
            <div class="otp-box">
                {otp}
            </div>
            
            <div class="info">
                <strong>⏰ Important:</strong> This OTP is valid for <strong>10 minutes</strong> only.
            </div>
            
            <p>Enter this code on the verification page to activate your account.</p>
            
            <p><strong>Security Tips:</strong></p>
            <ul>
                <li>Never share this OTP with anyone</li>
                <li>Our team will never ask for your OTP</li>
                <li>If you didn't request this, please ignore this email</li>
            </ul>
            
            <div class="footer">
                <p>This is an automated email, please do not reply.</p>
                <p>&copy; 2025 Quantum Blue. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return send_email(user_email, subject, html_content, 'otp_verification')

def send_welcome_email(user_email, user_name):
    """Send welcome email after successful verification"""
    subject = 'Welcome to Quantum Blue - Account Verified!'
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                padding: 30px;
                color: white;
            }}
            .content {{
                background-color: white;
                color: #333;
                border-radius: 8px;
                padding: 30px;
                margin-top: 20px;
            }}
            .success-icon {{
                text-align: center;
                font-size: 60px;
                margin: 20px 0;
            }}
            .feature {{
                background-color: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align: center; margin: 0;">🎉 Welcome Aboard!</h1>
            
            <div class="content">
                <div class="success-icon">✅</div>
                
                <h2 style="color: #28a745; text-align: center;">Account Successfully Verified!</h2>
                
                <p>Hello <strong>{user_name}</strong>,</p>
                
                <p>Congratulations! Your email has been verified and your account is now active.</p>
                
                <h3>What You Can Do Now:</h3>
                
                <div class="feature">
                    <strong>💬 Smart Conversations</strong><br>
                    Chat with our AI assistant powered by Azure OpenAI
                </div>
                
                <div class="feature">
                    <strong>📊 Data Insights</strong><br>
                    Get intelligent responses based on real-time data
                </div>
                
                <div class="feature">
                    <strong>📧 Conversation History</strong><br>
                    Export and email your chat history anytime
                </div>
                
                <div class="feature">
                    <strong>🔒 Secure & Private</strong><br>
                    Your data is protected with enterprise-grade security
                </div>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="#" style="display: inline-block; background-color: #007bff; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Start Chatting Now →
                    </a>
                </p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px; text-align: center;">
                    Need help? Contact us at <a href="mailto:{current_app.config['ADMIN_EMAIL']}">{current_app.config['ADMIN_EMAIL']}</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return send_email(user_email, subject, html_content, 'welcome')

def send_conversation_email(user_email, admin_email, conversation_data):
    """Send conversation summary to user and admin"""
    subject = f'Conversation Summary - {conversation_data["date"]}'
    
    # Create conversation HTML
    messages_html = ''
    for conv in conversation_data['conversations']:
        messages_html += f'''
        <div style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff;">
            <p style="margin: 0; color: #007bff; font-weight: bold;">
                <span style="background-color: #007bff; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px;">YOU</span>
            </p>
            <p style="margin: 10px 0; padding: 10px; background-color: white; border-radius: 4px;">{conv['user_message']}</p>
            
            <p style="margin: 15px 0 0 0; color: #28a745; font-weight: bold;">
                <span style="background-color: #28a745; color: white; padding: 4px 8px; border-radius: 3px; font-size: 12px;">AI ASSISTANT</span>
            </p>
            <p style="margin: 10px 0 0 0; padding: 10px; background-color: white; border-radius: 4px;">{conv['bot_response']}</p>
            
            <p style="margin: 10px 0 0 0; font-size: 12px; color: #666;">
                <em>Response time: {conv.get('response_time', 0):.2f}s</em>
            </p>
        </div>
        '''
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 30px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-box {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                border: 2px solid #e9ecef;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
            }}
            .stat-label {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">📊 Conversation Summary</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Your AI Chat History</p>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value">{len(conversation_data['conversations'])}</div>
                    <div class="stat-label">Total Messages</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{conversation_data['date']}</div>
                    <div class="stat-label">Date</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{conversation_data['user_name']}</div>
                    <div class="stat-label">User</div>
                </div>
            </div>
            
            <p><strong>📧 Email:</strong> {user_email}</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 2px solid #e9ecef;">
            
            <h2 style="color: #333; margin-bottom: 20px;">💬 Conversation History</h2>
            
            {messages_html}
            
            <hr style="margin: 30px 0; border: none; border-top: 2px solid #e9ecef;">
            
            <p style="text-align: center; color: #666; font-size: 14px;">
                This is an automated email from Quantum Blue. Please do not reply.<br>
                <em>Generated on {conversation_data['date']}</em>
            </p>
        </div>
    </body>
    </html>
    '''
    
    # Send to user
    send_email(user_email, subject, html_content, 'conversation')
    
    # Send to admin with [Admin] prefix
    send_email(admin_email, f'[Admin] {subject}', html_content, 'conversation_admin')