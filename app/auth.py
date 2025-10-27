from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from app import db
from app.models import User
from app.email_utils import send_otp_email, send_welcome_email
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('chatbot.chat'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        if not all([name, email, phone, password]):
            flash('All fields are required', 'error')
            return render_template('login.html')
        
        # Validate email format
        if '@' not in email or '.' not in email:
            flash('Invalid email format', 'error')
            return render_template('login.html')
        
        # Validate password strength
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('login.html')
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login or use a different email.', 'error')
            return render_template('login.html')
        
        try:
            # Create new user
            user = User(name=name, email=email, phone=phone)
            user.set_password(password)
            
            # Generate OTP
            otp = user.generate_otp()
            
            db.session.add(user)
            db.session.commit()
            
            # Send OTP email
            if send_otp_email(email, name, otp):
                # Store user_id in session for OTP verification
                session['pending_user_id'] = user.id
                session['otp_email'] = email
                
                flash('Registration successful! Please check your email for the OTP code.', 'success')
                return redirect(url_for('auth.verify_otp'))
            else:
                # If email sending fails, delete the user
                db.session.delete(user)
                db.session.commit()
                flash('Failed to send verification email. Please try again later.', 'error')
                return render_template('login.html')
        
        except Exception as e:
            db.session.rollback()
            logger.error(f'Registration error: {str(e)}')
            flash('Registration failed. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP code"""
    # Check if user is in verification process
    if 'pending_user_id' not in session:
        flash('No pending verification. Please register first.', 'warning')
        return redirect(url_for('auth.register'))
    
    user_id = session.get('pending_user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        flash('User not found. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    if user.email_verified:
        session.clear()
        flash('Email already verified. Please login.', 'info')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        
        if not otp:
            flash('Please enter the OTP code', 'error')
            return render_template('verify_otp.html', email=user.email)
        
        # Verify OTP
        if user.verify_otp(otp):
            # Mark email as verified
            user.verify_email()
            db.session.commit()
            
            # Send welcome email
            send_welcome_email(user.email, user.name)
            
            # Clear session
            session.pop('pending_user_id', None)
            session.pop('otp_email', None)
            
            flash('Email verified successfully! You can now login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'error')
            return render_template('verify_otp.html', email=user.email)
    
    return render_template('verify_otp.html', email=user.email)

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP code"""
    if 'pending_user_id' not in session:
        return jsonify({'error': 'No pending verification'}), 400
    
    user_id = session.get('pending_user_id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.email_verified:
        return jsonify({'error': 'Email already verified'}), 400
    
    try:
        # Generate new OTP
        otp = user.generate_otp()
        db.session.commit()
        
        # Send OTP email
        if send_otp_email(user.email, user.name, otp):
            flash('New OTP sent to your email', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Failed to send OTP. Please try again.', 'error')
            return redirect(url_for('auth.verify_otp'))
    
    except Exception as e:
        logger.error(f'Resend OTP error: {str(e)}')
        flash('Failed to resend OTP. Please try again.', 'error')
        return redirect(url_for('auth.verify_otp'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('chatbot.chat'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        if not user.email_verified:
            # Store user info for OTP verification
            session['pending_user_id'] = user.id
            session['otp_email'] = user.email
            
            # Generate and send new OTP
            otp = user.generate_otp()
            db.session.commit()
            send_otp_email(user.email, user.name, otp)
            
            flash('Please verify your email first. A new OTP has been sent.', 'warning')
            return redirect(url_for('auth.verify_otp'))
        
        # Login user
        login_user(user, remember=True)
        logger.info(f'User logged in: {user.email}')
        
        # Redirect to next page or chat
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('chatbot.chat'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    email = current_user.email
    logout_user()
    session.clear()
    logger.info(f'User logged out: {email}')
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - Send OTP for password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('chatbot.chat'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate OTP for password reset
            otp = user.generate_otp()
            db.session.commit()
            
            # Send OTP email
            if send_otp_email(user.email, user.name, otp):
                session['reset_user_id'] = user.id
                session['reset_email'] = email
                flash('Password reset OTP sent to your email', 'success')
                return redirect(url_for('auth.reset_password'))
            else:
                flash('Failed to send reset email. Please try again.', 'error')
        else:
            # Don't reveal if email exists or not (security best practice)
            flash('If this email exists, you will receive a password reset OTP', 'info')
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password with OTP verification"""
    if 'reset_user_id' not in session:
        flash('Please request a password reset first', 'warning')
        return redirect(url_for('auth.forgot_password'))
    
    user_id = session.get('reset_user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        flash('User not found. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not all([otp, new_password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('reset_password.html', email=user.email)
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', email=user.email)
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('reset_password.html', email=user.email)
        
        # Verify OTP
        if user.verify_otp(otp):
            # Update password
            user.set_password(new_password)
            user.otp_secret = None
            user.otp_created_at = None
            db.session.commit()
            
            # Clear session
            session.pop('reset_user_id', None)
            session.pop('reset_email', None)
            
            flash('Password reset successfully! Please login with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'error')
            return render_template('reset_password.html', email=user.email)
    
    return render_template('reset_password.html', email=user.email)