import os
import uuid
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database import db

# Setup Flask-Login
login_manager = LoginManager()

class AuthUser(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'auth_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # User sessions relationship
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class UserSession(db.Model):
    """Model for user sessions"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_users.id'), nullable=False)
    session_token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<Session {self.session_token[:8]}...>'

class PasswordReset(db.Model):
    """Model for password reset tokens"""
    __tablename__ = 'password_reset'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_users.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('AuthUser', backref=db.backref('reset_tokens', lazy=True))
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at or self.used
    
    def __repr__(self):
        return f'<PasswordReset {self.token[:8]}...>'

# Forms for authentication
class LoginForm(FlaskForm):
    """Form for user login"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = AuthUser.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already in use. Please choose a different one.')
    
    def validate_email(self, email):
        user = AuthUser.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email or sign in.')

class PasswordResetRequestForm(FlaskForm):
    """Form for requesting password reset"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class PasswordResetForm(FlaskForm):
    """Form for resetting password"""
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

# Create the auth blueprint
auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return AuthUser.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthUser.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Update last login time
            user.last_login = datetime.utcnow()
            
            # Create a new session if remember me is checked
            if form.remember_me.data:
                session_token = str(uuid.uuid4())
                expires_at = datetime.utcnow() + timedelta(days=30)
                
                user_session = UserSession(
                    user_id=user.id,
                    session_token=session_token,
                    expires_at=expires_at
                )
                db.session.add(user_session)
                
                # Set a cookie with the session token
                session['remember_token'] = session_token
            
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = AuthUser(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error registering user: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/signup.html', form=form)

@auth_bp.route('/logout')
def logout():
    # Remove the remember token if it exists
    if 'remember_token' in session:
        token = session.pop('remember_token')
        user_session = UserSession.query.filter_by(session_token=token).first()
        if user_session:
            db.session.delete(user_session)
            db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = AuthUser.query.filter_by(email=form.email.data).first()
        if user:
            # Create reset token
            token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Save token to database
            reset_token = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            db.session.add(reset_token)
            db.session.commit()
            
            # In a real app, send an email with the reset link
            # For this app, we'll just provide the link
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            flash(f'Password reset requested. In a real app, an email would be sent with instructions.', 'info')
            logging.info(f"Password reset URL: {reset_url}")
        else:
            # Don't reveal if email exists or not
            flash('If that email is registered, a password reset link will be sent.', 'info')
            
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Find the token in the database
    reset_record = PasswordReset.query.filter_by(token=token, used=False).first()
    
    if not reset_record or reset_record.is_expired():
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('auth.login'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = AuthUser.query.get(reset_record.user_id)
        if user:
            user.set_password(form.password.data)
            reset_record.used = True
            db.session.commit()
            flash('Your password has been updated! You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')

def init_auth(app):
    """Initialize authentication with the Flask app"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Setup the persistent login functionality
    @app.before_request
    def check_persistent_session():
        if not current_user.is_authenticated and 'remember_token' in session:
            token = session.get('remember_token')
            user_session = UserSession.query.filter_by(session_token=token).first()
            
            if user_session and not user_session.is_expired():
                user = AuthUser.query.get(user_session.user_id)
                if user:
                    login_user(user, remember=True)
            else:
                # Remove expired token
                session.pop('remember_token', None)