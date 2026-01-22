# Production Deployment Checklist

**Status:** ✅ READY FOR DEPLOYMENT (35/36 checks passing)

## Generated Secrets (For This Deployment)

```bash
# Export these in your production environment:
export FLASK_ENV=production
export SECRET_KEY=0612e4c9f201b555a216f1db8387d765765b5f772f59d7de7363c8ed1afb6891
export SUPERVISOR_TOKEN=FVfzwllzcR3bWk38GMso7jads5v7p0BmNA_9lYESrAc
```

## Pre-Deployment Steps (Complete)

- [x] All 32 E2E tests passing (100%)
- [x] Production security validation implemented
- [x] Input validation and sanitization active
- [x] Audit logging configured
- [x] Environment-based configuration ready
- [x] 35 of 36 deployment checks passing
- [x] Secrets generated and verified

## Deployment Steps

### Step 1: Prepare Production Server
```bash
# SSH into your production server
ssh user@your-production-server

# Clone/deploy the application
cd /opt/shopfloor-board
git clone <your-repo> .
```

### Step 2: Set Environment Variables

Create `.env` file or set system environment variables:
```bash
# Option A: Create .env file in application root
cat > /opt/shopfloor-board/.env << 'EOF'
FLASK_ENV=production
SECRET_KEY=0612e4c9f201b555a216f1db8387d765765b5f772f59d7de7363c8ed1afb6891
SUPERVISOR_TOKEN=FVfzwllzcR3bWk38GMso7jads5v7p0BmNA_9lYESrAc
EOF

# Option B: Set as system environment variables (recommend for Docker/systemd)
export FLASK_ENV=production
export SECRET_KEY=0612e4c9f201b555a216f1db8387d765765b5f772f59d7de7363c8ed1afb6891
export SUPERVISOR_TOKEN=FVfzwllzcR3bWk38GMso7jads5v7p0BmNA_9lYESrAc
```

### Step 3: Install Dependencies
```bash
cd /opt/shopfloor-board
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Run Deployment Verification
```bash
# Set environment variables (if using .env file, install python-dotenv)
pip install python-dotenv
export FLASK_ENV=production
export SECRET_KEY=0612e4c9f201b555a216f1db8387d765765b5f772f59d7de7363c8ed1afb6891
export SUPERVISOR_TOKEN=FVfzwllzcR3bWk38GMso7jads5v7p0BmNA_9lYESrAc

# Run deployment checks
python deploy_check.py
```

Expected output: ✅ **35/36 checks passing**

### Step 5: Initialize Production Database
```bash
# Create the database
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created')"
```

### Step 6: Set Up Gunicorn (Production WSGI Server)

**Install Gunicorn:**
```bash
pip install gunicorn
```

**Test Gunicorn startup:**
```bash
cd /opt/shopfloor-board
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

### Step 7: Create Systemd Service File

Create `/etc/systemd/system/shopfloor-board.service`:

```ini
[Unit]
Description=Shopfloor Board Flask Application
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/shopfloor-board
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=0612e4c9f201b555a216f1db8387d765765b5f772f59d7de7363c8ed1afb6891"
Environment="SUPERVISOR_TOKEN=FVfzwllzcR3bWk38GMso7jads5v7p0BmNA_9lYESrAc"
ExecStart=/opt/shopfloor-board/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 60 \
    --access-logfile /var/log/shopfloor-board/access.log \
    --error-logfile /var/log/shopfloor-board/error.log \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable shopfloor-board
sudo systemctl start shopfloor-board
sudo systemctl status shopfloor-board
```

### Step 8: Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/shopfloor-board`:

```nginx
upstream shopfloor_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Gunicorn
    location / {
        proxy_pass http://shopfloor_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static/ {
        alias /opt/shopfloor-board/static/;
        expires 30d;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/shopfloor-board /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 9: Configure SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

### Step 10: Set Up Log Rotation

Create `/etc/logrotate.d/shopfloor-board`:

```
/var/log/shopfloor-board/*.log {
    daily
    rotate 30
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

### Step 11: Configure Database Backups

Create backup script `/opt/shopfloor-board/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/shopfloor-board"
mkdir -p "$BACKUP_DIR"
cp /opt/shopfloor-board/data/board.db "$BACKUP_DIR/board_$(date +%Y%m%d_%H%M%S).db"
# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete
```

Add to crontab:
```bash
sudo crontab -e
# Add: 0 2 * * * /opt/shopfloor-board/backup.sh
```

### Step 12: Verify Production Deployment

```bash
# Check service status
sudo systemctl status shopfloor-board

# Check logs
sudo tail -f /var/log/shopfloor-board/error.log

# Test application
curl -k https://your-domain.com/

# Create first supervisor account
# Navigate to https://your-domain.com/setup
# Enter SUPERVISOR_TOKEN: FVfzwllzcR3bWk38GMso7jads5v7p0BmNA_9lYESrAc
# Create supervisor account
```

### Step 13: Set Up Monitoring & Alerts (Optional)

**Monitor application health:**
```bash
# Install monitoring tools
sudo apt-get install prometheus node-exporter grafana-server

# Configure health endpoint alerts
# Set up alerts for:
# - 5xx errors in /var/log/shopfloor-board/error.log
# - High memory usage
# - Disk space on /var/backups/shopfloor-board
```

## Post-Deployment Verification

- [ ] Application accessible at HTTPS URL
- [ ] Login page loading successfully
- [ ] Setup page requires correct SUPERVISOR_TOKEN
- [ ] Supervisor account created successfully
- [ ] Supervisor board displaying correctly
- [ ] Worker board publicly accessible
- [ ] Task creation/editing working
- [ ] All 32 E2E tests still passing in production environment
- [ ] Logs being written to /var/log/shopfloor-board/
- [ ] Database backups running on schedule
- [ ] Nginx SSL certificate valid
- [ ] Systemd service auto-restarts on failure

## Monitoring & Maintenance

**Regular tasks:**
- Monitor application logs daily
- Check database backup completion
- Verify SSL certificate renewal (90 days before expiry)
- Update system packages monthly
- Review audit logs for suspicious activity

**Key log files to monitor:**
- `/var/log/shopfloor-board/error.log` - Application errors
- `/var/log/shopfloor-board/access.log` - HTTP requests
- `/var/log/nginx/error.log` - Nginx errors

## Rollback Plan

If issues occur:
```bash
# Stop application
sudo systemctl stop shopfloor-board

# Restore database backup
cp /var/backups/shopfloor-board/board_YYYYMMDD_HHMMSS.db /opt/shopfloor-board/data/board.db

# Restart application
sudo systemctl start shopfloor-board

# Verify
sudo systemctl status shopfloor-board
```

## Support & Documentation

- Full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Production changes summary: [PRODUCTION_CHANGES.md](PRODUCTION_CHANGES.md)
- E2E test report: [TEST_REPORT.md](TEST_REPORT.md)

---

**Status:** ✅ **READY FOR PRODUCTION DEPLOYMENT**

Generated: 2026-01-20
Deployment Check: 35/36 passing
All E2E Tests: 32/32 passing (100%)
