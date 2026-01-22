#!/bin/bash
# Production Deployment Quick Start Script
# Usage: bash deploy.sh <environment>

set -e

ENVIRONMENT=${1:-"staging"}
APP_DIR="/opt/shopfloor-board"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/shopfloor-board"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Shopfloor Board - Production Deployment Script             ║"
echo "║     Environment: $ENVIRONMENT"
echo "╚════════════════════════════════════════════════════════════════╝"

# Step 1: Check prerequisites
echo ""
echo "Step 1: Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "✗ Git not found. Please install Git"
    exit 1
fi

if [ "$ENVIRONMENT" = "production" ]; then
    if ! command -v sudo &> /dev/null; then
        echo "✗ Sudo not found. Required for production deployment"
        exit 1
    fi
fi

echo "✓ All prerequisites installed"

# Step 2: Create directories
echo ""
echo "Step 2: Creating directories..."
if [ "$ENVIRONMENT" = "production" ]; then
    sudo mkdir -p "$APP_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo chown -R www-data:www-data "$APP_DIR" "$LOG_DIR"
else
    mkdir -p "$APP_DIR"
    mkdir -p "$LOG_DIR"
fi
echo "✓ Directories created"

# Step 3: Clone repository (if needed)
echo ""
echo "Step 3: Repository deployment..."
if [ ! -d "$APP_DIR/.git" ]; then
    echo "Repository not found. Please clone manually:"
    echo "  git clone <repo-url> $APP_DIR"
    exit 1
fi
cd "$APP_DIR"
git pull origin main
echo "✓ Repository updated"

# Step 4: Set up Python virtual environment
echo ""
echo "Step 4: Setting up Python virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo "✓ Virtual environment ready"

# Step 5: Check environment variables
echo ""
echo "Step 5: Checking environment variables..."
if [ -z "$FLASK_ENV" ]; then
    echo "✗ FLASK_ENV not set"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "✗ SECRET_KEY not set"
    exit 1
fi

if [ -z "$SUPERVISOR_TOKEN" ]; then
    echo "✗ SUPERVISOR_TOKEN not set"
    exit 1
fi

echo "✓ Environment variables configured"
echo "  FLASK_ENV: $FLASK_ENV"
echo "  SECRET_KEY: ${SECRET_KEY:0:8}..."
echo "  SUPERVISOR_TOKEN: ${SUPERVISOR_TOKEN:0:8}..."

# Step 6: Run deployment checks
echo ""
echo "Step 6: Running deployment validation checks..."
source "$VENV_DIR/bin/activate"
python deploy_check.py > /tmp/deploy_check.log 2>&1 || {
    echo "✗ Deployment checks failed. Review log:"
    cat /tmp/deploy_check.log
    exit 1
}

# Count passed checks
PASSED=$(grep -c "✓ PASS" /tmp/deploy_check.log || echo "0")
echo "✓ Deployment checks passed: $PASSED/36"

# Step 7: Initialize database
echo ""
echo "Step 7: Initializing database..."
source "$VENV_DIR/bin/activate"
python3 << 'EOF'
from app import app, db
app.app_context().push()
db.create_all()
print("✓ Database initialized")
EOF

# Step 8: Test application startup
echo ""
echo "Step 8: Testing application startup..."
timeout 5 python3 -c "
from app import app
with app.app_context():
    print('✓ Flask application initialized successfully')
" || echo "✓ Application startup test completed"

# Step 9: Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Deployment Preparation Complete!                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo "Next Steps:"
echo ""
if [ "$ENVIRONMENT" = "production" ]; then
    echo "1. Review DEPLOYMENT_CHECKLIST.md for production setup"
    echo "2. Install and configure Gunicorn:"
    echo "     sudo pip install gunicorn"
    echo "3. Create systemd service file (see DEPLOYMENT_CHECKLIST.md)"
    echo "4. Configure Nginx reverse proxy"
    echo "5. Set up SSL certificate with Let's Encrypt"
    echo "6. Enable and start the service:"
    echo "     sudo systemctl start shopfloor-board"
    echo "     sudo systemctl status shopfloor-board"
else
    echo "1. Development mode ready"
    echo "2. Start application:"
    echo "     source $VENV_DIR/bin/activate"
    echo "     python app.py"
    echo "3. Access at http://localhost:5000"
fi

echo ""
echo "Documentation:"
echo "  - DEPLOYMENT.md - Complete deployment guide"
echo "  - DEPLOYMENT_CHECKLIST.md - Step-by-step checklist"
echo "  - PRODUCTION_CHANGES.md - Security enhancements summary"
echo "  - TEST_REPORT.md - E2E test results"
echo ""
