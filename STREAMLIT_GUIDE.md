# 🎓 Scholarship Hunter - Web App Guide

## 🚀 Running Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
set -a; source .env; set +a
streamlit run streamlit_app.py
```

The app will open at: `http://localhost:8501`

## 🌐 Deploy to Streamlit Cloud (FREE)

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Streamlit web app"
git push origin main
```

### 2. Deploy on Streamlit Cloud
- Go to: https://streamlit.io/cloud
- Click "New app"
- Select your GitHub repo
- Main file path: `streamlit_app.py`
- Click "Deploy"

### 3. Add Secrets
In Streamlit Cloud:
1. Click Settings (gear icon)
2. Go to "Secrets"
3. Add your environment variables:

```
GEMINI_API_KEY=your_key
GOOGLE_SEARCH_API_KEY=your_key
GOOGLE_SEARCH_ENGINE_ID=your_id
SPREADSHEET_ID=your_id
GOOGLE_SHEETS_CREDS_B64=your_base64_encoded_json
```

To get base64 version of service account:
```bash
base64 -i service-account.json | pbcopy
```

Then paste as the value for `GOOGLE_SHEETS_CREDS_B64`.

### 4. Handle Credentials in Cloud
Add this to the top of `streamlit_app.py` (already included):

```python
import base64
import json
import os
from google.oauth2.service_account import Credentials

# Decode base64 credentials if in cloud
if 'GOOGLE_SHEETS_CREDS_B64' in os.environ:
    creds_b64 = os.environ.get('GOOGLE_SHEETS_CREDS_B64')
    creds_json = base64.b64decode(creds_b64).decode('utf-8')
    creds_dict = json.loads(creds_json)
```

## 📊 Features

### 📊 Dashboard
- Real-time metrics
- Visual charts of match scores
- Deadline timeline
- Full scholarship table

### 🔍 Run Search
- Custom search queries
- Adjustable results limit
- Live progress bar
- Real-time analysis

### 💾 Saved Scholarships
- Filter by match score
- Sort by deadline/date
- Expandable details for each scholarship
- Direct links to official pages

### 📈 Analytics
- Advanced statistics
- Score distribution
- Status breakdown
- Detailed visualizations

### ⚙️ Settings
- API key status check
- About & information
- Deployment guide

## 🎨 Custom Styling

The app uses:
- **Purple gradient theme** for a techy vibe
- **Plotly charts** for interactive visualizations
- **Streamlit components** for clean UI
- **Custom CSS** for enhanced styling

## 📱 Responsive Design

Works perfectly on:
- Desktop (1440px+)
- Tablet (768px-1024px)
- Mobile (320px-767px)

## 🔗 Share Your App

After deployment, Streamlit Cloud gives you a public URL like:
```
https://your-name-scholarship-hunter.streamlit.app
```

Perfect for:
- Portfolio projects
- Demo to recruiters
- Sharing with friends
- Including in GitHub README

## 💡 Pro Tips

1. **Faster page loads**: App caches Google Sheets data for 5 minutes
2. **Auto-refresh**: Secrets auto-update without redeployment
3. **GitHub integration**: Any push to main auto-deploys
4. **Free hosting**: Streamlit Cloud is completely free!

## 🐛 Troubleshooting

### App says "No scholarships found"
- Make sure you've run the bot (`python main.py`) at least once
- Check that your Google Sheet has data

### Charts not showing
- Ensure pandas & plotly are installed
- Run: `pip install --upgrade plotly pandas`

### Secrets not working in cloud
- Make sure environment variable names match exactly
- Clear browser cache and refresh

## 📚 Learn More

- Streamlit Docs: https://docs.streamlit.io
- Plotly Docs: https://plotly.com/python/
- Deployment Guide: https://docs.streamlit.io/deploy/streamlit-cloud

---

**Made with ❤️ for your portfolio!**
