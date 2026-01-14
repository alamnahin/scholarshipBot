#!/usr/bin/env python3
"""
Zero-Cost Scholarship Hunter Bot
Searches for fully funded Master's scholarships and matches them against your CV.
Uses free-tier APIs and can run on GitHub Actions.
"""

import base64
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# External libraries
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from thefuzz import fuzz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ScholarshipHunter:
    """Main class for scholarship hunting automation"""
    
    def __init__(self):
        """Initialize the bot with necessary credentials and configurations"""
        # Load environment variables
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self.google_search_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.google_sheets_creds = self._load_sheets_creds()
        
        # Validate required credentials
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        if not self.spreadsheet_id:
            raise ValueError("SPREADSHEET_ID environment variable not set")
        if not self.google_search_api_key:
            raise ValueError("GOOGLE_SEARCH_API_KEY environment variable not set")
        if not self.google_search_engine_id:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID environment variable not set")
        
        # Initialize Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
        
        # Initialize Google Sheets
        self.sheet = self._init_google_sheets()
        
        # Load CV
        self.cv_text = self._load_cv()
        
        # Configuration
        self.search_query = "fully funded msc in AI scholarship 2026 international"
        self.max_results = 10
        self.fuzzy_threshold = 85  # Similarity threshold for deduplication
        self.request_delay = 2  # Seconds between requests to be polite
        
    def _load_sheets_creds(self) -> Dict:
        """Load Google Sheets credentials from JSON, base64, or file path"""
        raw_json = os.getenv('GOOGLE_SHEETS_CREDS')
        b64_creds = os.getenv('GOOGLE_SHEETS_CREDS_B64')
        creds_path = os.getenv('GOOGLE_SHEETS_CREDS_PATH')

        if raw_json:
            try:
                return json.loads(raw_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"GOOGLE_SHEETS_CREDS is not valid JSON: {e}")

        if b64_creds:
            try:
                decoded = base64.b64decode(b64_creds)
                return json.loads(decoded)
            except Exception as e:
                raise ValueError(f"GOOGLE_SHEETS_CREDS_B64 is invalid: {e}")

        if creds_path:
            try:
                with open(creds_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                raise ValueError(f"Failed to read GOOGLE_SHEETS_CREDS_PATH: {e}")

        raise ValueError("Google Sheets credentials not provided. Set one of GOOGLE_SHEETS_CREDS (JSON string), GOOGLE_SHEETS_CREDS_B64 (base64), or GOOGLE_SHEETS_CREDS_PATH (file path).")

    def _init_google_sheets(self) -> gspread.Worksheet:
        """Initialize Google Sheets connection"""
        try:
            creds_dict = self.google_sheets_creds
            
            # Set up OAuth2 credentials
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            
            # Connect to Google Sheets
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            
            # Get or create the worksheet
            try:
                worksheet = spreadsheet.worksheet("Scholarships")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title="Scholarships",
                    rows=1000,
                    cols=10
                )
                # Add headers
                headers = [
                    "Date Found",
                    "Program Name",
                    "Application Deadline",
                    "Official URL",
                    "Match Score",
                    "Notes",
                    "Status"
                ]
                worksheet.append_row(headers)
            
            logger.info("Successfully connected to Google Sheets")
            return worksheet
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            raise
    
    def _load_cv(self) -> str:
        """Load CV text from local file"""
        try:
            cv_path = os.path.join(os.path.dirname(__file__), 'cv.md')
            with open(cv_path, 'r', encoding='utf-8') as f:
                cv_text = f.read()
            
            if not cv_text.strip():
                raise ValueError("CV file is empty")
            
            logger.info(f"Loaded CV ({len(cv_text)} characters)")
            return cv_text
            
        except FileNotFoundError:
            logger.error("cv.md file not found in the script directory")
            raise
        except Exception as e:
            logger.error(f"Failed to load CV: {e}")
            raise
    
    def search_scholarships(self) -> List[Dict[str, str]]:
        """Search for scholarships using Google Custom Search API"""
        logger.info(f"Searching for: {self.search_query}")
        results = []
        
        try:
            # Initialize Google Custom Search
            service = build('customsearch', 'v1', developerKey=self.google_search_api_key)
            
            # Execute search
            search_result = service.cse().list(
                q=self.search_query,
                cx=self.google_search_engine_id,
                num=min(self.max_results, 10)  # Google limits to 10 per request
            ).execute()
            
            # Parse results
            items = search_result.get('items', [])
            for item in items:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                })
            
            logger.info(f"Found {len(results)} search results")
            return results
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("Google Search API quota exceeded. You have 100 queries/day limit.")
                logger.info("💡 Tip: The script runs once per day, so you should have plenty of quota.")
            else:
                logger.error(f"Google Search API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_existing_entries(self) -> List[Dict[str, str]]:
        """Fetch existing entries from Google Sheets for deduplication"""
        try:
            records = self.sheet.get_all_records()
            logger.info(f"Loaded {len(records)} existing entries from database")
            return records
        except Exception as e:
            logger.error(f"Failed to fetch existing entries: {e}")
            return []
    
    def is_duplicate(self, url: str, program_name: str, existing_entries: List[Dict]) -> bool:
        """Check if scholarship already exists using fuzzy matching"""
        for entry in existing_entries:
            existing_url = entry.get('Official URL', '')
            existing_name = entry.get('Program Name', '')
            
            # Check URL exact match
            if url == existing_url:
                logger.info(f"Duplicate found (URL match): {url}")
                return True
            
            # Check program name fuzzy match
            if program_name and existing_name:
                similarity = fuzz.ratio(program_name.lower(), existing_name.lower())
                if similarity >= self.fuzzy_threshold:
                    logger.info(f"Duplicate found (fuzzy match {similarity}%): {program_name}")
                    return True
        
        return False
    
    def scrape_page(self, url: str) -> Optional[str]:
        """Scrape text content from a URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = ' '.join(text.split())
            
            # Limit text length to avoid token limits (keep first 8000 chars)
            text = text[:8000]
            
            logger.info(f"Scraped {len(text)} characters from {url}")
            return text
            
        except requests.RequestException as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None
    
    def analyze_with_gemini(self, scholarship_text: str, url: str) -> Optional[Dict]:
        """Analyze scholarship page with Gemini AI to extract relevant information"""
        prompt = f"""You are an expert scholarship advisor. Analyze the following scholarship opportunity against the candidate's CV.

**CANDIDATE'S CV:**
{self.cv_text}

**SCHOLARSHIP PAGE TEXT:**
{scholarship_text}

**YOUR TASK:**
1. Determine if this is a FULLY FUNDED Master's scholarship (tuition + living expenses covered)
2. Check if the candidate is eligible based on their CV
3. Extract key details

**RESPONSE FORMAT (JSON ONLY):**
If this is a fully funded Master's scholarship that matches the candidate's profile, respond with:
{{
  "is_match": true,
  "program_name": "Exact program name",
  "deadline": "Application deadline (format: YYYY-MM-DD or 'Not specified')",
  "official_url": "{url}",
  "match_score": 85,
  "notes": "Brief explanation of why this fits the candidate's profile and any special requirements"
}}

If it's NOT a match (not fully funded, not Master's level, candidate not eligible, or insufficient information), respond with:
{{
  "is_match": false,
  "reason": "Brief explanation"
}}

Respond ONLY with valid JSON. No other text.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to parse JSON response
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            if result.get('is_match'):
                logger.info(f"✓ Match found: {result.get('program_name')}")
                return result
            else:
                logger.info(f"✗ Not a match: {result.get('reason')}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
    
    def save_to_database(self, match: Dict) -> bool:
        """Save a matched scholarship to Google Sheets"""
        try:
            row = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                match.get('program_name', ''),
                match.get('deadline', ''),
                match.get('official_url', ''),
                str(match.get('match_score', '')),
                match.get('notes', ''),
                'New'
            ]
            
            self.sheet.append_row(row)
            logger.info(f"✓ Saved to database: {match.get('program_name')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            return False
    
    def run(self):
        """Main execution flow"""
        logger.info("=" * 70)
        logger.info("🎓 SCHOLARSHIP HUNTER BOT STARTED")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        try:
            # Step 1: Get existing entries for deduplication
            existing_entries = self.get_existing_entries()
            
            # Step 2: Search for scholarships
            search_results = self.search_scholarships()
            
            if not search_results:
                logger.warning("No search results found")
                return
            
            # Step 3: Process each result
            matches_found = 0
            processed = 0
            
            for idx, result in enumerate(search_results, 1):
                logger.info(f"\n--- Processing result {idx}/{len(search_results)} ---")
                logger.info(f"Title: {result['title']}")
                logger.info(f"URL: {result['url']}")
                
                # Check for duplicate (preliminary check with title)
                if self.is_duplicate(result['url'], result['title'], existing_entries):
                    logger.info("⊘ Skipping duplicate")
                    continue
                
                # Scrape the page
                page_text = self.scrape_page(result['url'])
                if not page_text:
                    logger.warning("⊘ Skipping - failed to scrape")
                    continue
                
                processed += 1
                
                # Analyze with Gemini
                match = self.analyze_with_gemini(page_text, result['url'])
                
                if match:
                    # Double-check for duplicates with extracted program name
                    if self.is_duplicate(result['url'], match.get('program_name', ''), existing_entries):
                        logger.info("⊘ Skipping duplicate (detected after analysis)")
                        continue
                    
                    # Save to database
                    if self.save_to_database(match):
                        matches_found += 1
                        # Add to existing entries to prevent duplicates in same run
                        existing_entries.append(match)
                
                # Be polite - delay between requests
                if idx < len(search_results):
                    time.sleep(self.request_delay)
            
            # Summary
            elapsed = time.time() - start_time
            logger.info("\n" + "=" * 70)
            logger.info("📊 SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Search results: {len(search_results)}")
            logger.info(f"Pages processed: {processed}")
            logger.info(f"New matches found: {matches_found}")
            logger.info(f"Execution time: {elapsed:.2f} seconds")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Fatal error in main execution: {e}")
            raise


def main():
    """Entry point for the script"""
    try:
        hunter = ScholarshipHunter()
        hunter.run()
        logger.info("✓ Bot completed successfully")
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("\n⊘ Interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"✗ Bot failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
