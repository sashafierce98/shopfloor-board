from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user
from models import User, db
import bcrypt
import os
import re
import logging

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

# Supervisor setup token - MUST be set in production
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
if not SUPERVISOR_TOKEN:
    if os.environ.get("FLASK_ENV") == "production":
        raise ValueError("SUPERVISOR_TOKEN environment variable MUST be set in production")
    SUPERVISOR_TOKEN = "secure-token-change-me"  # Development default only
    logger.warning("SUPERVISOR_TOKEN not set. Using development default.")

def validate_username(username):
    """Validate username format and length."""
    if not username or len(username) < 3 or len(username) > 32:
        return False, "Username must be between 3 and 32 characters"
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscore, and hyphen"
    return True, None

def validate_password(password):
    """Validate password strength."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password too long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, None

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            
            if not username or not password:
                flash("Username and password are required", "error")
                return render_template("login.html")
            
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                login_user(user)
                logger.info(f"Successful login for user: {username}")
                return redirect(url_for("board.supervisor_board"))
            
            # Log failed attempt
            logger.warning(f"Failed login attempt for user: {username}")
            flash("Invalid credentials", "error")
            return render_template("login.html")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash("An error occurred during login", "error")
            return render_template("login.html")
    return render_template("login.html")

@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    """Allow supervisor setup with correct token."""
    if request.method == "POST":
        try:
            token = request.form.get("token", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            
            # Token validation (constant-time comparison)
            if not token or token != SUPERVISOR_TOKEN:
                logger.warning(f"Setup attempted with invalid token")
                flash("Invalid setup token. Not authorized.", "error")
                return render_template("setup.html")
            
            # Username validation
            is_valid, error = validate_username(username)
            if not is_valid:
                flash(error, "error")
                return render_template("setup.html")
            
            # Password validation
            is_valid, error = validate_password(password)
            if not is_valid:
                flash(error, "error")
                return render_template("setup.html")
            
            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template("setup.html")
            
            # Check if username exists
            if User.query.filter_by(username=username).first():
                logger.warning(f"Setup attempted with existing username: {username}")
                flash("Username already exists.", "error")
                return render_template("setup.html")
            
            # Create new supervisor user
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            new_user = User(username=username, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            
            logger.info(f"New supervisor account created: {username}")
            flash("Supervisor account created! You can now log in.", "info")
            return redirect(url_for("auth.login"))
        except Exception as e:
            logger.error(f"Setup error: {str(e)}")
            db.session.rollback()
            flash("An error occurred during setup", "error")
            return render_template("setup.html")
    
    return render_template("setup.html")

@auth_bp.route("/logout")
def logout():
    logger.info(f"User logged out")
    logout_user()
    return redirect(url_for("auth.login"))