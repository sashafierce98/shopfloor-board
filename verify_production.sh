#!/bin/bash
# TGP Bioplastics Shopfloor Board - Production Deployment Verification
# Run this script with production environment variables set

echo "=========================================="
echo "PRODUCTION DEPLOYMENT VERIFICATION"
echo "=========================================="
echo ""

# Check required environment variables
echo "1. Checking environment variables..."
missing_vars=0

if [ -z "$FLASK_ENV" ] || [ "$FLASK_ENV" != "production" ]; then
    echo "✗ FLASK_ENV not set to 'production'"
    missing_vars=$((missing_vars + 1))
else
    echo "✓ FLASK_ENV=production"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "✗ SECRET_KEY not set"
    missing_vars=$((missing_vars + 1))
else
    echo "✓ SECRET_KEY set (${#SECRET_KEY} characters)"
fi

if [ -z "$SUPERVISOR_TOKEN" ]; then
    echo "✗ SUPERVISOR_TOKEN not set"
    missing_vars=$((missing_vars + 1))
else
    echo "✓ SUPERVISOR_TOKEN set"
fi

echo ""
echo "2. Checking directory structure..."
cd "$(dirname "$0")" || exit 1

for dir in data static templates; do
    if [ -d "$dir" ]; then
        echo "✓ Directory exists: $dir/"
    else
        echo "✗ Directory missing: $dir/"
        missing_vars=$((missing_vars + 1))
    fi
done

echo ""
echo "3. Checking required files..."
for file in app.py auth.py board.py models.py requirements.txt; do
    if [ -f "$file" ]; then
        echo "✓ File exists: $file"
    else
        echo "✗ File missing: $file"
        missing_vars=$((missing_vars + 1))
    fi
done

echo ""
echo "4. Checking Python dependencies..."
python3 -c "import flask, flask_login, flask_sqlalchemy, bcrypt" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ All Python dependencies installed"
else
    echo "✗ Missing Python dependencies"
    echo "  Run: pip install -r requirements.txt"
    missing_vars=$((missing_vars + 1))
fi

echo ""
echo "5. Checking code security..."
if grep -r "secure-token-change-me" *.py --exclude=deploy_check.py > /dev/null 2>&1; then
    if [ "$FLASK_ENV" = "production" ]; then
        echo "✗ Default token found in code (production detected)"
        missing_vars=$((missing_vars + 1))
    else
        echo "⚠ Default token found (acceptable in development)"
    fi
else
    echo "✓ No hardcoded default tokens"
fi

echo ""
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="

if [ $missing_vars -eq 0 ]; then
    echo "✓ All production requirements met"
    echo "✓ DEPLOYMENT APPROVED"
    exit 0
else
    echo "✗ $missing_vars issue(s) found"
    echo "✗ Please resolve before deploying"
    exit 1
fi
