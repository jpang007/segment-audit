#!/usr/bin/env python3
"""
Gemini REST API client - bypasses SSL certificate issues with gRPC
"""

import requests
import json
from typing import Dict, Any


class GeminiRESTClient:
    """Direct REST API client for Gemini - no gRPC/SSL issues"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def generate_content(self, prompt: str, model: str = "gemini-2.0-flash-exp") -> str:
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

        response = requests.post(url, json=payload, headers=headers, timeout=60)
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


# Test
if __name__ == '__main__':
    import os

    api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyDvVcIeKWD3c0qzEteaVbvmKXWg1AAlNKU')

    client = GeminiRESTClient(api_key)

    print("Testing Gemini REST API client...")

    test_prompt = """Respond with this JSON:
{
  "status": "success",
  "message": "REST API is working!"
}"""

    try:
        response = client.generate_content(test_prompt)
        print(f"\n✓ Response received: {len(response)} chars")
        print(f"\nResponse:\n{response}")

        # Try parsing as JSON
        result = json.loads(response)
        print(f"\n✓ JSON parse successful: {result}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
