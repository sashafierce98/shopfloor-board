# Railway Deployment Guide

**Shopfloor Board - Deploy via Railway**

This guide will help you deploy the application to Railway using GitHub.

---

## Prerequisites

- GitHub account with this repository
- Railway account (https://railway.app)
- Git installed locally

---

## Step-by-Step Deployment

### Step 1: Create GitHub Repository

1. Create a new repository on GitHub (private or public)
2. Clone this repository locally (if not already done):
   ```bash
   git clone <your-github-repo-url>
   cd shopfloor-board
   ```

3. Add all files and commit:
   ```bash
   git add .
   git commit -m "Initial commit - Shopfloor Board application"
   git push origin main
   ```

### Step 2: Connect to Railway

1. Go to https://railway.app and sign in with GitHub
2. Click **"New Project"** or **"Create"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub repositories
5. Select the `shopfloor-board` repository
6. Railway will auto-detect the Python app and start deployment

### Step 3: Configure Environment Variables

Railway automatically reads environment variables. Set these in the Railway dashboard:

1. In Railway project, go to **Variables**
2. Add the following variables:

   ```
   FLASK_ENV=production
   SECRET_KEY=<generate-new-random-key>
   SUPERVISOR_TOKEN=<generate-new-random-token>
   DATABASE_URL=<optional-postgresql-url>
   ```

   **Generate new secrets:**
   ```bash
   # On your local machine
   python3 -c "import os; print('SECRET_KEY:', os.urandom(32).hex())"
   python3 -c "import secrets; print('SUPERVISOR_TOKEN:', secrets.token_urlsafe(32))"
   ```

3. Copy the generated values into Railway Variables

### Step 4: (Optional) Add PostgreSQL Database

For production, use PostgreSQL instead of SQLite:

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway automatically adds `DATABASE_URL` variable
4. Update `app.py` to use PostgreSQL connection string:

   ```python
   import os
   
   # In app.py, around line 10:
   if os.environ.get('DATABASE_URL'):
       # Use PostgreSQL
       db_url = os.environ.get('DATABASE_URL')
       if db_url.startswith('postgres://'):
           db_url = db_url.replace('postgres://', 'postgresql://', 1)
       app.config['SQLALCHEMY_DATABASE_URI'] = db_url
   else:
       # Use SQLite
       app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/board.db'
   ```

### Step 5: Deploy

Once environment variables are set, Railway will:

1. Detect the changes
2. Install dependencies from `requirements.txt`
3. Run `Procfile` command: `gunicorn --workers 4 --bind 0.0.0.0:$PORT app:app`
4. Start the application
5. Provide you with a public URL

### Step 6: Verify Deployment

1. Click the deployment link in Railway dashboard
2. You should see the login page
3. Navigate to `/setup` to create supervisor account
4. Use your `SUPERVISOR_TOKEN` to create account

---

## Troubleshooting

### Build Fails

**Check the logs:**
- Railway dashboard → Logs tab
- Look for dependency errors or Python syntax issues

**Common issues:**
- Missing `Procfile` - Already included ✓
- Missing dependencies in `requirements.txt` - Already included ✓
- Wrong Python version - Specified in `runtime.txt` ✓

### Application Won't Start

Check Railway logs for:
- Missing environment variables
- Database connection errors
- Permission issues

### Database Issues

If using SQLite on Railway (not recommended for production):
- Data will be lost on redeploy
- Use PostgreSQL service instead (see Step 4)

---

## File Structure for Railway

```
shopfloor-board/
├── Procfile                         ← Railway uses this ✓
├── railway.json                     ← Alternative config ✓
├── runtime.txt                      ← Specifies Python 3.11 ✓
├── requirements.txt                 ← All dependencies ✓
├── .gitignore                       ← Excludes unnecessary files ✓
├── .railwayignore                   ← Railway-specific ignores ✓
│
├── app.py                           ← Main Flask app
├── auth.py                          ← Authentication
├── board.py                         ← Task management
├── models.py                        ← Database models
│
├── templates/                       ← HTML templates
├── static/                          ← CSS and assets
├── data/                            ← Database storage
│
└── ... (all other files included)
```

---

## Environment Variables Reference

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `FLASK_ENV` | Yes | `production` | Flask environment |
| `SECRET_KEY` | Yes | `<64-hex-chars>` | Session encryption |
| `SUPERVISOR_TOKEN` | Yes | `<url-safe-token>` | Setup authentication |
| `DATABASE_URL` | No | `postgresql://...` | PostgreSQL connection |

---

## Post-Deployment

### Initialize Database (First Time Only)

If using SQLite:
- Database auto-creates on first run

If using PostgreSQL:
1. SSH into Railway or use Railway CLI
2. Initialize database:
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

### Create Supervisor Account

1. Go to your Railway URL + `/setup`
2. Enter `SUPERVISOR_TOKEN` from environment variables
3. Create supervisor username and password
4. Log in and start managing tasks

### Monitor Application

Railway dashboard shows:
- Live logs
- Memory/CPU usage
- Deployment history
- Error tracking

---

## Automatic Deployments

Railway automatically deploys when you:
- Push to `main` branch
- Merge pull requests
- Update environment variables

No additional action needed!

---

## Rollback

To rollback to previous deployment:
1. Railway dashboard → Deployments
2. Find previous successful deployment
3. Click the three dots → Redeploy
4. Confirm rollback

---

## Scaling

As traffic grows:
1. Railway dashboard → Resources
2. Increase Memory/CPU allocation
3. Increase worker count in `Procfile`:
   ```
   web: gunicorn --workers 8 --bind 0.0.0.0:$PORT app:app
   ```

---

## Support & Documentation

- Railway Docs: https://docs.railway.app
- Flask Docs: https://flask.palletsprojects.com
- Gunicorn Docs: https://gunicorn.org
- This project: See [README.md](README.md) and [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

## Quick Reference Commands

```bash
# Clone and setup locally
git clone <your-repo>
cd shopfloor-board

# Test locally before pushing
python app.py

# Generate new secrets
python3 -c "import os; print(os.urandom(32).hex())"
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Push to GitHub (triggers Railway deployment)
git push origin main

# View Railway logs
railway logs
```

---

**Status: ✅ Ready for Railway Deployment**

Your repository is configured and ready to deploy directly from GitHub to Railway!

Next steps:
1. Push to GitHub
2. Connect to Railway
3. Set environment variables
4. Deploy! 🚀
