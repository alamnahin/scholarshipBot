#!/bin/bash
# Quick verification script for Google Custom Search setup

echo "🔍 Checking Google Custom Search Configuration..."
echo ""

# Check if API key is set
if [ -z "$GOOGLE_SEARCH_API_KEY" ]; then
    echo "❌ GOOGLE_SEARCH_API_KEY is not set"
else
    echo "✅ GOOGLE_SEARCH_API_KEY is set: ${GOOGLE_SEARCH_API_KEY:0:20}..."
fi

# Check if Search Engine ID is set
if [ -z "$GOOGLE_SEARCH_ENGINE_ID" ]; then
    echo "❌ GOOGLE_SEARCH_ENGINE_ID is not set"
else
    echo "✅ GOOGLE_SEARCH_ENGINE_ID is set: $GOOGLE_SEARCH_ENGINE_ID"
fi

echo ""
echo "🧪 Testing API Key with a simple request..."
echo ""

# Test the API with curl
RESPONSE=$(curl -s "https://www.googleapis.com/customsearch/v1?q=test&cx=${GOOGLE_SEARCH_ENGINE_ID}&key=${GOOGLE_SEARCH_API_KEY}")

# Check if there's an error
if echo "$RESPONSE" | grep -q "error"; then
    echo "❌ API Test Failed!"
    echo ""
    echo "Error details:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    echo ""
    echo "📋 Troubleshooting steps:"
    echo "1. Go to: https://console.cloud.google.com/apis/library/customsearch.googleapis.com"
    echo "2. Make sure 'Custom Search API' is ENABLED"
    echo "3. Check your API key at: https://console.cloud.google.com/apis/credentials"
    echo "4. If you just created the key, wait 5 minutes for it to activate"
    echo "5. Make sure there are no API key restrictions blocking the Custom Search API"
else
    echo "✅ API Test Successful!"
    echo ""
    echo "Sample result:"
    echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"  - Found {len(data.get('items', []))} results\")" 2>/dev/null || echo "  - Response received"
fi

echo ""
echo "Done!"
