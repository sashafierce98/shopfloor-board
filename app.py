import os
import logging
from flask import Flask
from flask_login import LoginManager
from models import db, User
from auth import auth_bp
from board import board_bp

app = Flask(__name__)

# Security Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24).hex())
if not os.environ.get("SECRET_KEY"):
    print("WARNING: SECRET_KEY not set. Using randomly generated key. Set SECRET_KEY env var in production.")

# Environment detection
IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "board.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = IS_PRODUCTION  # HTTPS only in production
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF protection
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour session timeout

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DATA_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)
app.logger.info(f"Application starting in {'PRODUCTION' if IS_PRODUCTION else 'DEVELOPMENT'} mode")

print("Using database at:", DB_PATH)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(board_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)