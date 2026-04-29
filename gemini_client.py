#!/usr/bin/env python3
"""
Gemini API Client - Works locally with SSL bypass and on Render with proper SSL
"""

import os
import json
import requests
from typing import Dict, Any


class GeminiClient:
    """
    Unified Gemini client that works both locally and on production
    - Local: Uses REST API with SSL verification disabled (dev only)
    - Production: Uses proper SSL verification
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

        # Development mode: Disable SSL verification for local testing only
        # This is detected by checking if we're running on Render (has DATABASE_URL env var)
        self.is_dev_mode = os.environ.get('DATABASE_URL') is None

        if self.is_dev_mode:
            print("⚠️  DEV MODE: SSL verification disabled for local testing")
            # Suppress urllib3 SSL warnings in dev mode
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def generate_content(self, prompt: str, model: str = "gemini-2.0-flash") -> str:
        """
        Generate content using Gemini REST API
        Returns the response text
        """
        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        # In dev mode, disable SSL verification
        # In production (Render), use proper SSL verification
        verify_ssl = not self.is_dev_mode

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60,
                verify=verify_ssl  # False in dev, True in production
            )
            response.raise_for_status()

            result = response.json()

            # Extract text from response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        return parts[0]['text']

            raise ValueError(f"Unexpected response format: {result}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Gemini API call failed: {str(e)}")


# Test
if __name__ == '__main__':
    import os

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Usage: export GEMINI_API_KEY='your-key-here' && python3 gemini_client.py")
        exit(1)

    client = GeminiClient(api_key)

    print("Testing Gemini client...")
    print(f"Dev mode: {client.is_dev_mode}")

    test_prompt = """Respond with this JSON:
{
  "status": "success",
  "message": "Client is working!",
  "test_number": 42
}"""

    try:
        response = client.generate_content(test_prompt)
        print(f"\n✓ Response received: {len(response)} chars")
        print(f"\nResponse:\n{response}")

        # Try parsing as JSON
        result = json.loads(response)
        print(f"\n✓ JSON parse successful!")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
