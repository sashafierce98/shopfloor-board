# TGP Bioplastics Shopfloor Board - Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Shopfloor Board application to a production environment.

## Pre-Deployment Checklist

### 1. Generate Secure Credentials

Before deployment, generate strong credentials:

```bash
# Generate SECRET_KEY (32+ random bytes)
python3 -c "import os; print('SECRET_KEY=' + os.urandom(32).hex())"

# Generate SUPERVISOR_TOKEN
python3 -c "import secrets; print('SUPERVISOR_TOKEN=' + secrets.token_urlsafe(32))"
```

### 2. Environment Variables

Create a `.env` file in production with:

```bash
export FLASK_ENV=production
export FLASK_APP=app.py
export SECRET_KEY=<your-generated-secret-key>
export SUPERVISOR_TOKEN=<your-generated-supervisor-token>
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Security Enhancements Made

### Authentication
- ✓ Token-based setup prevents unauthorized supervisor creation
- ✓ Strong password validation (8+ chars, uppercase, lowercase, numbers)
- ✓ Username validation (alphanumeric, 3-32 chars)
- ✓ bcrypt password hashing with random salt

### Input Validation
- ✓ Sanitization of user input to prevent XSS
- ✓ Priority validation (restricted to: low, medium, high, critical)
- ✓ Status validation (restricted to: not_started, active, scheduled, done)
- ✓ Date format validation

### Session Security
- ✓ HTTP-only cookies (prevents JavaScript access)
- ✓ Secure flag (HTTPS only in production)
- ✓ SameSite=Lax (CSRF protection)
- ✓ 1-hour session timeout

### Audit Logging
- ✓ All user actions logged with timestamps
- ✓ Login attempts (success and failure)
- ✓ Task creation/modification/deletion
- ✓ Status changes
- ✓ Account creation

## Deployment Steps

### Option 1: Production Server with Gunicorn (Recommended)

```bash
# Install production WSGI server
pip install gunicorn

# Start with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 60 --access-logfile - app:app

# Or with systemd service file:
```

Create `/etc/systemd/system/shopfloor-board.service`:

```ini
[Unit]
Description=TGP Bioplastics Shopfloor Board
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/shopfloor-board
Environment="PATH=/var/www/shopfloor-board/venv/bin"
Environment="FLASK_ENV=production"
Environment="FLASK_APP=app.py"
EnvironmentFile=/etc/shopfloor-board/.env
ExecStart=/var/www/shopfloor-board/venv/bin/gunicorn -w 4 -b localhost:5000 --timeout 60 --access-logfile /var/log/shopfloor-board/access.log app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable shopfloor-board
sudo systemctl start shopfloor-board
```

### Option 2: Nginx Reverse Proxy

Configure `/etc/nginx/sites-available/shopfloor-board`:

```nginx
upstream shopfloor {
    server localhost:5000;
}

server {
    listen 443 ssl http2;
    server_name shopfloor.tgpbioplastics.com;
    
    ssl_certificate /etc/letsencrypt/live/shopfloor.tgpbioplastics.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shopfloor.tgpbioplastics.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://shopfloor;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/shopfloor-board/static/;
        expires 30d;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name shopfloor.tgpbioplastics.com;
    return 301 https://$server_name$request_uri;
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/shopfloor-board /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## Running Deployment Checks

```bash
# Set environment variables
export FLASK_ENV=production
export SECRET_KEY=<your-secret-key>
export SUPERVISOR_TOKEN=<your-supervisor-token>

# Run sanity checks
python deploy_check.py
```

Expected output:
```
✓ All critical checks passed
✓ Deployment Status: APPROVED
```

## Initial Supervisor Setup

1. Access `https://shopfloor.tgpbioplastics.com/auth/setup`
2. Enter the SUPERVISOR_TOKEN
3. Create supervisor username and password (must meet strength requirements)
4. Redirect to login page

**Important:** The setup endpoint will be disabled after the first supervisor account is created.

## Monitoring & Maintenance

### Logs
- Application logs: `/var/log/shopfloor-board/app.log`
- Access logs: `/var/log/shopfloor-board/access.log`
- System logs: `journalctl -u shopfloor-board -f`

### Log Rotation
Create `/etc/logrotate.d/shopfloor-board`:

```
/var/log/shopfloor-board/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload shopfloor-board > /dev/null 2>&1 || true
    endscript
}
```

### Database Backups

Daily backup script `/usr/local/bin/backup-shopfloor.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/shopfloor-board"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /var/www/shopfloor-board/data/board.db $BACKUP_DIR/board_$DATE.db
find $BACKUP_DIR -name "board_*.db" -mtime +30 -delete
```

Add to crontab:
```
0 2 * * * /usr/local/bin/backup-shopfloor.sh
```

## Security Hardening

### Firewall Rules
```bash
# Allow HTTPS only
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp  # For redirect only
sudo ufw deny 5000/tcp
```

### Database Security
- Use PostgreSQL for large deployments
- Regular backups to external storage
- Encrypted database credentials

### Access Control
- Restrict IP addresses if possible
- Use VPN for remote access
- Regular security audits

## Testing Deployment

After deployment, run sanity checks:

```bash
python deploy_check.py
```

Verify:
- ✓ All files in place
- ✓ Environment variables set
- ✓ Dependencies installed
- ✓ Database initialized
- ✓ SSL certificate valid

## Rollback Procedure

If issues occur:

```bash
# Stop the service
sudo systemctl stop shopfloor-board

# Restore backup
cp /var/backups/shopfloor-board/board_BACKUP_DATE.db /var/www/shopfloor-board/data/board.db

# Restart
sudo systemctl start shopfloor-board

# Verify
curl https://shopfloor.tgpbioplastics.com/auth/setup
```

## Support & Documentation

- **Test Report:** `TEST_REPORT.md`
- **Architecture:** See `models.py`
- **API Routes:** See `auth.py` and `board.py`
- **Logs:** Check `/var/log/shopfloor-board/app.log`

## Production Configuration Summary

| Setting | Development | Production |
|---------|-------------|-----------|
| FLASK_ENV | development | production |
| DEBUG | True | False |
| SECRET_KEY | Hard-coded | Environment variable |
| SUPERVISOR_TOKEN | Hard-coded default | Environment variable |
| SESSION_COOKIE_SECURE | False | True |
| Database | SQLite | SQLite/PostgreSQL |
| WSGI Server | Flask dev server | Gunicorn |
| Reverse Proxy | None | Nginx |
| HTTPS | No | Yes |
| Logging | Console | File + Console |

---

**Version:** 1.0  
**Last Updated:** January 20, 2026
