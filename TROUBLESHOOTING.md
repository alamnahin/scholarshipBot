# Troubleshooting Guide

## DuckDuckGo Rate Limit (202 Error)

**Problem:** `Search failed: ... 202 Ratelimit`

**Why it happens:**
- DuckDuckGo detects automated/bot traffic and blocks the request
- Too many requests from the same IP in a short time
- Common when running the script multiple times quickly

**Solutions (try in order):**

### 1. Wait and Retry (Easiest)
```bash
# Wait 5-10 minutes, then try again
sleep 600 && python main.py
```

### 2. Use a VPN or Different Network
- Connect to a VPN
- Switch from WiFi to mobile hotspot
- Run from a different location

### 3. Use Proxies (Advanced)
Update the search function to use rotating proxies:
```python
# In search_scholarships() method
with DDGS(proxies={'http': 'http://your-proxy:port'}) as ddgs:
    ...
```

### 4. Reduce Search Frequency
In [main.py](main.py#L67):
```python
self.max_results = 5  # Reduce from 10 to 5
```

### 5. Alternative: Manual Test Mode
Create a test file with sample URLs to verify the rest of the pipeline works:

```python
# test_urls.json
[
  {
    "title": "MIT AI Scholarship 2026",
    "url": "https://example.com/scholarship",
    "snippet": "Fully funded MSc in AI"
  }
]
```

Then modify `main.py` to load from this file instead of searching.

### 6. GitHub Actions Will Work Better
When deployed to GitHub Actions:
- Runs from GitHub's datacenter IPs (different from yours)
- Runs once per day (less likely to hit limits)
- More likely to succeed consistently

## Other Common Issues

### "Failed to initialize Google Sheets"
- Verify [service-account.json](service-account.json) is valid JSON
- Check that the Google Sheet is shared with the service account email
- Ensure both Sheets API and Drive API are enabled in Google Cloud Console

### "cv.md file not found"
- Ensure [cv.md](cv.md) exists in the project root
- Check file permissions: `ls -la cv.md`

### "No search results found"
- This is expected if DuckDuckGo rate limit occurs
- Try the solutions above

## Testing Without Search

To test the scraping/analysis/saving pipeline without hitting rate limits:

```python
# Quick test script: test_scrape.py
from main import ScholarshipHunter

hunter = ScholarshipHunter()

# Test with a known scholarship page
test_url = "https://www.daad.de/en/study-and-research-in-germany/scholarships/"
page_text = hunter.scrape_page(test_url)
if page_text:
    result = hunter.analyze_with_gemini(page_text, test_url)
    if result:
        hunter.save_to_database(result)
        print("✓ Test successful!")
```

Run: `python test_scrape.py`

## Need More Help?

1. Check the logs for specific error messages
2. Verify all environment variables are set: `echo $GEMINI_API_KEY`
3. Test internet connectivity: `curl -I https://duckduckgo.com`
4. For GitHub Actions issues, check the Actions tab in your repository
