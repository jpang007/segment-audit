# Deployment Guide - Segment Audit Dashboard

This guide will help you deploy your Flask app to the web for free!

---

## 🚀 Quick Deploy to Render (Recommended)

**Render is the best free option for this Flask app** - it supports background processes, persistent storage, and is very easy to setup.

### Prerequisites
- GitHub account
- All your files in a GitHub repository

### Step 1: Push Code to GitHub

```bash
cd /Users/jpang

# Initialize git if not already done
git init

# Create .gitignore
cat > .gitignore << 'GITIGNORE'
audit_data/
__pycache__/
*.pyc
.DS_Store
*.egg-info/
dist/
build/
GITIGNORE

# Add and commit files
git add .
git commit -m "Initial commit - Segment Audit Dashboard"

# Create GitHub repo (or use GitHub website)
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. **Go to** [render.com](https://render.com) and sign up (free)

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repository**

4. **Configure the service:**
   - **Name:** segment-audit-dashboard (or your choice)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free

5. **Add Environment Variables** (if needed):
   - No environment variables needed for basic deployment

6. **Click "Create Web Service"**

7. **Wait 2-3 minutes** for deployment

8. **Your app will be live at:** `https://segment-audit-dashboard.onrender.com`

### Important Notes for Render:
- ✅ Free tier includes 750 hours/month
- ⚠️ App sleeps after 15 minutes of inactivity
- ⚠️ First request after sleep takes ~30 seconds to wake up
- ✅ Persistent disk storage available (512MB free)
- ✅ Automatic HTTPS

---

## 🚂 Alternative: Deploy to Railway

Railway is another great free option with $5 free credit per month.

### Steps:

1. **Go to** [railway.app](https://railway.app) and sign up

2. **Click "New Project" → "Deploy from GitHub repo"**

3. **Select your repository**

4. **Railway auto-detects Python and deploys!**

5. **Click "Settings" → "Generate Domain"** to get your URL

That's it! Railway automatically:
- Installs dependencies from requirements.txt
- Runs with gunicorn
- Provides a public URL

---

## 🐍 Alternative: PythonAnywhere

Good for simpler Flask apps, but has limitations with background threads.

### Steps:

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload your files** via Files tab

3. **Open Bash console** and run:
```bash
pip install --user -r requirements.txt
```

4. **Web tab** → "Add a new web app"
   - Choose Flask
   - Set path to your app.py

5. **Configure WSGI file** to point to your app

**Note:** PythonAnywhere free tier doesn't support background workers well.

---

## 📦 Files Created for Deployment

### `requirements.txt`
All Python dependencies needed to run the app.

### `Procfile`
Tells hosting services how to run your app:
```
web: gunicorn app:app
```

### Updated `app.py`
Now uses environment PORT variable:
```python
port = int(os.environ.get('PORT', 5001))
```

---

## 🔧 Testing Deployment Locally

Before deploying, test that gunicorn works:

```bash
# Install gunicorn
pip install gunicorn

# Test locally
gunicorn app:app

# Visit http://localhost:8000
```

---

## 🌐 Custom Domain (Optional)

All services above allow you to:
1. Buy a custom domain (like segmentaudit.com)
2. Point it to your deployment
3. Get automatic HTTPS

---

## 💡 Tips for Production

### 1. Security
- The app already has SSL bypass option for VPN users
- Use HTTPS (provided automatically by all platforms)
- Don't commit sensitive data to GitHub

### 2. Performance
- Free tiers sleep after inactivity
- Consider upgrading for always-on service
- Render: $7/month for always-on
- Railway: Pay per use after free credit

### 3. Storage
- `audit_data/` folder stores CSV/JSON results
- On free tiers, this resets when app restarts
- Upgrade for persistent storage if needed

---

## 🐛 Troubleshooting

### App doesn't start
- Check build logs on platform
- Verify requirements.txt has all dependencies
- Ensure Procfile is correct

### "Application Error"
- Check application logs
- Verify environment variables
- May need to increase memory (upgrade)

### Slow to load
- Free tiers sleep after 15 min inactivity
- First load takes ~30 seconds
- Subsequent loads are fast

---

## 📞 Need Help?

- **Render docs:** https://render.com/docs
- **Railway docs:** https://docs.railway.app
- **PythonAnywhere docs:** https://help.pythonanywhere.com

---

**Ready to deploy? Follow the Render steps above!** 🚀
