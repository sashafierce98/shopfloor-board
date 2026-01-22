#!/usr/bin/env python3
"""
TGP Bioplastics Shopfloor Board - Deployment Sanity Check Script
Verifies all production requirements are met before deployment
"""

import os
import sys
import json
import subprocess
from datetime import datetime

# Color codes for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class DeploymentChecker:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.start_time = datetime.now()
    
    def check(self, name, condition, critical=True, details=""):
        """Record a check result"""
        status = "✓ PASS" if condition else "✗ FAIL"
        color = GREEN if condition else (RED if critical else YELLOW)
        level = "CRITICAL" if critical and not condition else ("WARNING" if not condition else "OK")
        
        check_result = {
            "name": name,
            "status": "PASS" if condition else "FAIL",
            "critical": critical,
            "details": details,
            "level": level
        }
        self.checks.append(check_result)
        
        print(f"{color}{status}{RESET} {level:8} | {name}")
        if details:
            print(f"  └─ {details}")
        
        if condition:
            self.passed += 1
        else:
            if critical:
                self.failed += 1
            else:
                self.warnings += 1
    
    def section(self, title):
        """Print section header"""
        print(f"\n{BLUE}{'='*70}")
        print(f"{title}")
        print(f"{'='*70}{RESET}\n")
    
    def summary(self):
        """Print summary report"""
        self.section("DEPLOYMENT SANITY CHECK SUMMARY")
        
        total = len(self.checks)
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f"Total Checks:     {total}")
        print(f"✓ Passed:         {self.passed}")
        print(f"✗ Critical Failed: {self.failed}")
        print(f"⚠ Warnings:       {self.warnings}")
        print(f"Execution Time:   {elapsed:.2f}s")
        
        status = "APPROVED" if self.failed == 0 else "FAILED"
        status_color = GREEN if self.failed == 0 else RED
        print(f"\n{status_color}Deployment Status: {status}{RESET}")
        
        if self.failed > 0:
            print(f"\n{RED}CRITICAL ISSUES MUST BE RESOLVED BEFORE DEPLOYMENT{RESET}")
        elif self.warnings > 0:
            print(f"\n{YELLOW}WARNING: Address recommendations before deploying to production{RESET}")
        else:
            print(f"\n{GREEN}All checks passed. Application ready for deployment.{RESET}")
        
        return status == "APPROVED"

def main():
    checker = DeploymentChecker()
    base_dir = "/Users/mrinmayee/Desktop/shopfloor-board"
    
    # --- ENVIRONMENT CHECKS ---
    checker.section("1. ENVIRONMENT & CONFIGURATION")
    
    # Check Flask environment
    flask_env = os.environ.get("FLASK_ENV", "development")
    checker.check(
        "FLASK_ENV is set to production",
        flask_env == "production",
        critical=False,
        details=f"Current: {flask_env}"
    )
    
    # Check SECRET_KEY
    secret_key = os.environ.get("SECRET_KEY")
    checker.check(
        "SECRET_KEY environment variable is set",
        secret_key is not None,
        critical=True,
        details="Required for session security"
    )
    
    if secret_key:
        checker.check(
            "SECRET_KEY is strong (min 32 chars)",
            len(secret_key) >= 32,
            critical=True,
            details=f"Current length: {len(secret_key)} chars"
        )
    
    # Check SUPERVISOR_TOKEN
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
    checker.check(
        "SUPERVISOR_TOKEN environment variable is set",
        supervisor_token is not None,
        critical=True,
        details="Required to prevent unauthorized account creation"
    )
    
    if supervisor_token:
        checker.check(
            "SUPERVISOR_TOKEN is not default value",
            supervisor_token != "secure-token-change-me",
            critical=True,
            details="Must not use development default in production"
        )
    
    # --- FILE SYSTEM CHECKS ---
    checker.section("2. FILE SYSTEM & DIRECTORIES")
    
    # Check required files
    required_files = {
        "app.py": "Main Flask application",
        "auth.py": "Authentication module",
        "board.py": "Board/task management module",
        "models.py": "Database models",
        "requirements.txt": "Python dependencies",
        "static/styles.css": "Application CSS",
        "static/logo.jpg": "TGP Bioplastics logo",
        "templates/login.html": "Login page template",
        "templates/setup.html": "Setup page template",
        "templates/supervisor_board.html": "Supervisor dashboard template",
        "templates/public_board.html": "Public worker board template",
    }
    
    for file_path, description in required_files.items():
        full_path = os.path.join(base_dir, file_path)
        exists = os.path.exists(full_path)
        checker.check(
            f"File exists: {file_path}",
            exists,
            critical=True,
            details=description
        )
    
    # Check directories
    required_dirs = {
        "data": "Database storage",
        "static": "Static files",
        "templates": "HTML templates",
    }
    
    for dir_name, description in required_dirs.items():
        dir_path = os.path.join(base_dir, dir_name)
        exists = os.path.isdir(dir_path)
        checker.check(
            f"Directory exists: {dir_name}/",
            exists,
            critical=True,
            details=description
        )
    
    # --- DEPENDENCIES CHECK ---
    checker.section("3. PYTHON DEPENDENCIES")
    
    required_packages = ["flask", "flask-login", "flask-sqlalchemy", "bcrypt"]
    
    try:
        requirements_file = os.path.join(base_dir, "requirements.txt")
        if os.path.exists(requirements_file):
            with open(requirements_file, 'r') as f:
                requirements = f.read().lower()
            
            for package in required_packages:
                checker.check(
                    f"Dependency listed: {package}",
                    package in requirements,
                    critical=True
                )
    except Exception as e:
        checker.check(
            "Requirements file readable",
            False,
            critical=True,
            details=str(e)
        )
    
    # --- CODE QUALITY CHECKS ---
    checker.section("4. CODE SECURITY & QUALITY")
    
    # Check for hardcoded secrets in code
    files_to_check = [
        os.path.join(base_dir, "app.py"),
        os.path.join(base_dir, "auth.py"),
        os.path.join(base_dir, "board.py"),
    ]
    
    hardcoded_secrets = []
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                if "secure-token-change-me" in content:
                    hardcoded_secrets.append(file_path)
    
    checker.check(
        "No hardcoded default tokens in code",
        len(hardcoded_secrets) == 0,
        critical=True,
        details=f"Allowed in development defaults only"
    )
    
    # Check for password validation
    auth_file = os.path.join(base_dir, "auth.py")
    if os.path.exists(auth_file):
        with open(auth_file, 'r') as f:
            auth_content = f.read()
        
        checker.check(
            "Password validation implemented",
            "validate_password" in auth_content,
            critical=True,
            details="Should enforce strong passwords"
        )
        
        checker.check(
            "Username validation implemented",
            "validate_username" in auth_content,
            critical=True,
            details="Should prevent invalid usernames"
        )
    
    # Check for logging
    board_file = os.path.join(base_dir, "board.py")
    if os.path.exists(board_file):
        with open(board_file, 'r') as f:
            board_content = f.read()
        
        checker.check(
            "Audit logging implemented",
            "logger.info" in board_content or "logger.warning" in board_content,
            critical=True,
            details="Should log user actions for audit trail"
        )
    
    # --- DATABASE CHECKS ---
    checker.section("5. DATABASE CONFIGURATION")
    
    app_file = os.path.join(base_dir, "app.py")
    if os.path.exists(app_file):
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        checker.check(
            "SQLAlchemy track modifications disabled",
            "SQLALCHEMY_TRACK_MODIFICATIONS" in app_content and "False" in app_content,
            critical=False,
            details="Improves performance, not critical for security"
        )
    
    data_dir = os.path.join(base_dir, "data")
    data_dir_exists = os.path.isdir(data_dir)
    checker.check(
        "Data directory exists",
        data_dir_exists,
        critical=False,
        details="Will be created on first run if missing"
    )
    
    # --- SECURITY CONFIGURATION ---
    checker.section("6. SECURITY HEADERS & CONFIGURATION")
    
    if os.path.exists(app_file):
        with open(app_file, 'r') as f:
            app_content = f.read()
        
        checker.check(
            "SESSION_COOKIE_HTTPONLY enabled",
            "SESSION_COOKIE_HTTPONLY" in app_content and "True" in app_content,
            critical=True,
            details="Prevents XSS attacks accessing session cookies"
        )
        
        checker.check(
            "SESSION_COOKIE_SAMESITE configured",
            "SESSION_COOKIE_SAMESITE" in app_content,
            critical=True,
            details="CSRF protection"
        )
        
        checker.check(
            "SESSION_COOKIE_SECURE for HTTPS",
            "SESSION_COOKIE_SECURE" in app_content and "IS_PRODUCTION" in app_content,
            critical=True,
            details="Should be enabled only over HTTPS"
        )
    
    # --- UI/UX CHECKS ---
    checker.section("7. UI & BRANDING")
    
    # Check logo file
    logo_path = os.path.join(base_dir, "static", "logo.jpg")
    checker.check(
        "Logo file present",
        os.path.exists(logo_path),
        critical=False,
        details="TGP Bioplastics branding"
    )
    
    # Check CSS file
    css_path = os.path.join(base_dir, "static", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        checker.check(
            "TGP Bioplastics colors in CSS",
            "#00a878" in css_content,
            critical=False,
            details="Primary brand color"
        )
    
    # --- DOCUMENTATION CHECKS ---
    checker.section("8. DOCUMENTATION & CONFIGURATION")
    
    test_report = os.path.join(base_dir, "TEST_REPORT.md")
    checker.check(
        "Test report exists",
        os.path.exists(test_report),
        critical=False,
        details="E2E testing documentation"
    )
    
    env_template = os.path.join(base_dir, ".env.production")
    checker.check(
        "Production environment template exists",
        os.path.exists(env_template),
        critical=False,
        details="Guide for environment configuration"
    )
    
    # --- RECOMMENDATIONS ---
    checker.section("9. DEPLOYMENT RECOMMENDATIONS")
    
    recommendations = [
        ("Use a reverse proxy (Nginx/Apache)", "For production traffic"),
        ("Enable HTTPS with SSL certificate", "For secure connections"),
        ("Set up log rotation", "For app.log file management"),
        ("Configure database backups", "Regular SQLite backups"),
        ("Set up monitoring/alerts", "For uptime and error tracking"),
        ("Use production WSGI server", "Gunicorn or uWSGI instead of Flask development server"),
        ("Configure firewall rules", "Restrict access to necessary ports"),
        ("Implement rate limiting", "For login endpoint protection"),
    ]
    
    print(f"{BLUE}Recommended Actions:{RESET}")
    for i, (action, details) in enumerate(recommendations, 1):
        print(f"  {i}. {action}")
        print(f"     └─ {details}\n")
    
    # --- FINAL SUMMARY ---
    is_approved = checker.summary()
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": checker.checks,
        "summary": {
            "total": len(checker.checks),
            "passed": checker.passed,
            "critical_failed": checker.failed,
            "warnings": checker.warnings,
        },
        "deployment_approved": is_approved,
        "recommendations": recommendations
    }
    
    report_file = os.path.join(base_dir, "deployment_check.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return 0 if is_approved else 1

if __name__ == "__main__":
    sys.exit(main())
