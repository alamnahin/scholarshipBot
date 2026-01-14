# 🎓 Zero-Cost Scholarship Hunter Bot

A production-ready Python automation that searches for fully funded Master's scholarships, compares them against your CV, and saves matches to Google Sheets. Runs daily on GitHub Actions with **zero infrastructure costs**.

## ✨ Features

- 🔍 **Reliable Search**: Uses Google Custom Search (100 free queries/day, perfect for once-daily runs)
- 🤖 **AI-Powered Matching**: Gemini 1.5 Flash analyzes CV fit and extracts details
- 🛡️ **Deduplication**: Fuzzy string matching prevents duplicate entries
- 📊 **Google Sheets Database**: Free, accessible anywhere
- ⚡ **Automated**: Runs daily via GitHub Actions with zero rate-limiting issues
- 💰 **100% Free**: No paid APIs or services

## 📋 Requirements

- Python 3.11+
- Google Account (for Sheets + Custom Search)
- Gemini API Key (free tier)
- GitHub Account (for automation)
- Google Custom Search Engine (free to create)

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd scholarshipBot
pip install -r requirements.txt
```

### 2. Set Up Google Custom Search API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Custom Search API**:
   - Search for "Custom Search API"
   - Click "Enable"
4. Create API credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "+ Create Credentials" → "API Key"
   - Copy your **API Key** (this is `GOOGLE_SEARCH_API_KEY`)

5. Create a Custom Search Engine:
   - Go to [Programmable Search Engine](https://programmablesearchengine.google.com/cse/all)
   - Click "Create" or "Add"
   - Configure search to cover "entire web"
   - Click "Create"
   - Find the **Search Engine ID** (cx parameter) - this is `GOOGLE_SEARCH_ENGINE_ID`
   - Free tier: 100 queries/day (perfect for once-daily runs)

### 3. Set Up Google Sheets

1. Go to [Google Cloud Console](https://console.cloud.google.com/) (same project)
2. Enable **Google Sheets API** and **Google Drive API**
3. Create a **Service Account**:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it (e.g., "scholarship-bot")
   - Grant role: "Editor"
   - Click "Create Key" → Choose "JSON"
   - Download the JSON file

4. Create a new Google Sheet:
   - Go to [Google Sheets](https://sheets.google.com)
   - Create a blank spreadsheet
   - Copy the **Spreadsheet ID** from the URL:
     ```
     https://docs.google.com/spreadsheets/d/1abc123xyz/edit
                                              ^^^^^ this part
     ```
   - Share the sheet with the service account email (found in JSON file)
     - Give "Editor" access

### 4. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key

### 5. Configure Environment Variables

**For Local Testing:**

```bash
cp .env.example .env
# Edit .env with your actual credentials:
# - GEMINI_API_KEY
# - GOOGLE_SEARCH_API_KEY
# - GOOGLE_SEARCH_ENGINE_ID
# - GOOGLE_SHEETS_CREDS_PATH (path to service-account.json)
# - SPREADSHEET_ID
```

**For GitHub Actions:**

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `GOOGLE_SEARCH_API_KEY`: Your Custom Search API key
   - `GOOGLE_SEARCH_ENGINE_ID`: Your Custom Search Engine ID
   - `GOOGLE_SHEETS_CREDS_B64`: Base64-encoded service account JSON
     ```bash
     # To encode locally:
     base64 -i service-account.json | pbcopy
     # Then paste in GitHub Secrets
     ```
   - `SPREADSHEET_ID`: Your Google Sheets ID

### 6. Prepare Your CV

Edit [cv.md](cv.md) with your actual CV content in plain text/markdown format.

### 7. Test Locally

```bash
# Load environment variables (if using .env file)
set -a; source .env; set +a

# Run the bot
python main.py
```

### 8. Deploy to GitHub Actions

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Initial scholarship bot setup"
   git push origin main
   ```

2. The bot will now run automatically every day at 9:00 AM UTC

3. To trigger manually:
   - Go to "Actions" tab in your repository
   - Select "Daily Scholarship Hunter"
   - Click "Run workflow"

## 📁 Project Structure

```
scholarshipBot/
├── main.py                 # Main bot script
├── cv.md                   # Your CV (plain text)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .github/
│   └── workflows/
│       └── daily.yml      # GitHub Actions workflow
└── README.md             # This file
```

## 🔧 Configuration

Edit these variables in `main.py` if needed:

```python
self.search_query = "fully funded msc in AI scholarship 2026 international"
self.max_results = 10              # Number of search results to process
self.fuzzy_threshold = 85          # Similarity % for duplicate detection
self.request_delay = 2             # Seconds between requests
```

## 📊 Output Format

The bot saves matches to Google Sheets with these columns:

| Date Found | Program Name | Application Deadline | Official URL | Match Score | Notes | Status |
|------------|-------------|---------------------|--------------|-------------|-------|--------|
| 2026-01-14 | MIT AI Fellowship | 2026-03-15 | https://... | 92 | Strong match due to... | New |

## 🛠️ Troubleshooting

### "Failed to initialize Google Sheets"
- Verify service account JSON is valid
- Check if sheet is shared with service account email
- Ensure both Sheets API and Drive API are enabled

### "GEMINI_API_KEY not set"
- Verify environment variable is set correctly
- For GitHub Actions, check repository secrets

### "cv.md file not found"
- Ensure cv.md exists in the same directory as main.py
- Check file permissions

### Rate Limiting
- The script includes delays to respect rate limits
- If you get blocked, increase `self.request_delay`

## 🔒 Security Best Practices

1. **Never commit**:
   - `.env` file
   - Service account JSON files
   - API keys

2. **GitHub Secrets**:
   - Use repository secrets for all credentials
   - Never print secrets in logs

3. **Service Account**:
   - Only grant minimum required permissions
   - Rotate keys periodically

## 📈 Customization

### Change Search Query

Edit in `main.py`:
```python
self.search_query = "your custom search query here"
```

### Adjust Gemini Prompt

Modify the prompt in the `analyze_with_gemini()` method to change extraction logic.

### Change Schedule

Edit `.github/workflows/daily.yml`:
```yaml
schedule:
  - cron: '0 9 * * *'  # Change time/frequency
```

Cron format: `minute hour day month weekday`
- `0 9 * * *` = 9:00 AM UTC daily
- `0 */6 * * *` = Every 6 hours
- `0 9 * * 1` = 9:00 AM UTC every Monday

## 📝 API Limits (Free Tier)

- **Google Custom Search**: **100 queries/day** (perfect for 1 daily run!)
- **Gemini 1.5 Flash**: 15 requests/minute, 1500 requests/day
- **Google Sheets API**: 300 requests/minute

No rate limiting issues anymore! The 100 queries/day limit is plenty for once-daily searches.

## 🤝 Contributing

Feel free to fork and customize for your needs!

## 📄 License

MIT License - Use freely for personal or commercial projects.

## 🙏 Acknowledgments

Built with:
- [duckduckgo-search](https://github.com/deedy5/duckduckgo_search)
- [google-generativeai](https://github.com/google/generative-ai-python)
- [gspread](https://github.com/burnash/gspread)
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
- [thefuzz](https://github.com/seatgeek/thefuzz)

---

**Happy Scholarship Hunting! 🎯**
