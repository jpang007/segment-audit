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

    def generate_content(self, prompt: str, model: str = "gemini-2.0-flash", max_retries: int = 4) -> str:
        """
        Generate content using Gemini REST API with intelligent retry logic

        Retry strategy:
        - 503, 500, 504, 429: Retryable (service issues, rate limits)
        - 400, 401, 403, 404: Non-retryable (client errors)
        - Uses exponential backoff with jitter
        - Automatic model fallback on persistent failures

        Returns the response text
        """
        import random
        import time

        # Model fallback chain
        models_to_try = [model]
        if model == "gemini-2.5-flash":
            models_to_try.extend(["gemini-2.0-flash", "gemini-2.0-flash-lite"])
        elif model == "gemini-2.0-flash":
            models_to_try.append("gemini-2.0-flash-lite")

        last_error = None
        prompt_size = len(prompt)
        print(f"   📊 Prompt size: {prompt_size:,} characters")

        for model_idx, model_name in enumerate(models_to_try):
            url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"

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
                    "maxOutputTokens": 16384,  # Increased from 8192 to handle longer responses
                }
            }

            headers = {
                "Content-Type": "application/json"
            }

            # In dev mode, disable SSL verification
            # In production (Render), use proper SSL verification
            verify_ssl = not self.is_dev_mode

            # Try with retries and exponential backoff
            for attempt in range(max_retries):
                try:
                    print(f"   🤖 Calling {model_name} (attempt {attempt + 1}/{max_retries})")
                    start_time = time.time()

                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=180,  # 3 minutes for complex audits
                        verify=verify_ssl
                    )

                    elapsed = time.time() - start_time
                    status_code = response.status_code

                    print(f"   📡 Response: {status_code} in {elapsed:.1f}s")

                    # Check for retryable errors
                    if status_code in [429, 500, 503, 504]:
                        # Retryable: rate limit or service issues
                        if attempt < max_retries - 1:
                            # Exponential backoff with jitter: base * 2^attempt + random(0-2s)
                            base_wait = 5 if status_code == 429 else 2
                            wait_time = base_wait * (2 ** attempt) + random.uniform(0, 2)
                            wait_time = min(wait_time, 120)  # Cap at 2 minutes

                            error_names = {429: "Rate limited", 500: "Server error", 503: "Service unavailable", 504: "Gateway timeout"}
                            print(f"   ⚠️  {error_names.get(status_code, status_code)} - waiting {wait_time:.1f}s before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            last_error = Exception(f"Failed after {max_retries} attempts with status {status_code}")
                            break  # Try next model

                    # Non-retryable errors
                    elif status_code in [400, 401, 403, 404]:
                        error_msg = f"{status_code} error (non-retryable)"
                        try:
                            error_detail = response.json()
                            error_msg += f": {error_detail}"
                        except:
                            error_msg += f": {response.text[:200]}"
                        print(f"   ❌ {error_msg}")
                        last_error = Exception(error_msg)
                        break  # Don't retry, don't try other models

                    # Success
                    response.raise_for_status()
                    result = response.json()

                    # Extract text from response
                    if 'candidates' in result and len(result['candidates']) > 0:
                        candidate = result['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            parts = candidate['content']['parts']
                            if len(parts) > 0 and 'text' in parts[0]:
                                response_text = parts[0]['text']
                                print(f"   ✅ Success: {len(response_text):,} chars returned")
                                if attempt > 0 or model_idx > 0:
                                    print(f"   ℹ️  Used fallback: {model_name} after {attempt + 1} attempts")
                                return response_text

                    # Unexpected format
                    raise ValueError(f"Unexpected response format from Gemini")

                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        wait_time = 2 * (2 ** attempt) + random.uniform(0, 2)
                        print(f"   ⏱️  Timeout - retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        last_error = Exception("Request timed out after multiple attempts")
                        break

                except requests.exceptions.RequestException as e:
                    print(f"   ❌ Request exception: {str(e)[:200]}")
                    if attempt < max_retries - 1:
                        wait_time = 2 * (2 ** attempt) + random.uniform(0, 2)
                        print(f"   🔄 Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        last_error = Exception(f"Request failed: {str(e)}")
                        break

                except Exception as e:
                    print(f"   ❌ Unexpected error: {str(e)[:200]}")
                    last_error = e
                    break

            # Log model fallback
            if model_idx > 0:
                print(f"   🔀 Falling back from {models_to_try[model_idx-1]} to {model_name}")

        # All models exhausted
        print(f"   ❌ All {len(models_to_try)} model(s) failed")
        if last_error:
            raise last_error
        raise Exception("All Gemini API attempts exhausted across all fallback models")

    def staged_summarization(self, structured_data: dict, goal: str, business_context: str, model: str = "gemini-2.5-flash") -> dict:
        """
        Multi-stage summarization to reduce prompt size and improve reliability

        Stage 1: Source/Schema Summary
        Stage 2: Destination Summary
        Stage 3: Audience/Activation Summary
        Stage 4: Final Analysis (using compact summaries)

        Returns final analysis result
        """
        import json

        print("   🔄 Starting staged summarization...")

        # Stage 1: Source & Schema Summary
        print("   📊 Stage 1/4: Summarizing sources and schema...")
        source_summary_prompt = f"""Analyze and summarize source health and schema quality.

**Data:**
```json
{{
  "sources": {json.dumps(structured_data.get('source_insights', [])[:30], indent=2)},
  "schema_health": {json.dumps(structured_data.get('schema_health', {}), indent=2)}
}}
```

**Output:** Return JSON with:
- source_count (total sources)
- healthy_sources (count)
- problematic_sources (list of {{name, issue}})
- schema_issues (list of sources with >1000 events)
- top_concerns (3 bullet points)

Keep response under 500 characters."""

        source_summary = self.generate_content(source_summary_prompt, model=model)
        print(f"   ✓ Stage 1 complete: {len(source_summary)} chars")

        # Stage 2: Destination Summary
        print("   📍 Stage 2/4: Summarizing destinations...")
        dest_summary_prompt = f"""Analyze and summarize destination coverage.

**Data:**
```json
{{
  "destinations": {json.dumps(structured_data.get('destination_summary', {}), indent=2)}
}}
```

**Output:** Return JSON with:
- total_destinations
- by_category ({{email: count, analytics: count, ...}})
- coverage_assessment (string)

Keep response under 300 characters."""

        dest_summary = self.generate_content(dest_summary_prompt, model=model)
        print(f"   ✓ Stage 2 complete: {len(dest_summary)} chars")

        # Stage 3: Audience & Activation Summary
        print("   👥 Stage 3/4: Summarizing audiences and journeys...")
        audience_summary_prompt = f"""Analyze and summarize audience activation.

**Data:**
```json
{{
  "audiences": {json.dumps(structured_data.get('audience_insights', [])[:50], indent=2)},
  "journeys": {json.dumps(structured_data.get('journey_insights', {}), indent=2)},
  "profile_insights": {json.dumps(structured_data.get('profile_insights', {}), indent=2)}
}}
```

**Output:** Return JSON with:
- total_audiences
- unactivated_count
- journey_maturity (none/exploring/emerging/advanced)
- profile_resolution_enabled (boolean)
- top_opportunities (3 bullet points)

Keep response under 500 characters."""

        audience_summary = self.generate_content(audience_summary_prompt, model=model)
        print(f"   ✓ Stage 3 complete: {len(audience_summary)} chars")

        # Stage 4: Final Analysis (using compact summaries)
        print("   🎯 Stage 4/4: Generating final recommendations...")

        compact_data = {
            "source_summary": source_summary,
            "destination_summary": dest_summary,
            "audience_summary": audience_summary,
            "workspace_summary": structured_data.get('workspace_summary', {}),
            "business_context": business_context
        }

        return {"compact_summaries": compact_data}


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
