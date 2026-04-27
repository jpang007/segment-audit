#!/usr/bin/env python3
"""
Gemini API Summarizer - Turns structured findings into polished recommendations
Uses Google's Gemini Flash model (free tier) for cost-effective summarization
"""

import json
import os
from typing import Dict, Any, Optional

try:
    import google.genai as genai
    GENAI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_AVAILABLE = True
    except ImportError:
        GENAI_AVAILABLE = False
        genai = None


class GeminiSummarizer:
    """Summarizes audit findings using Gemini API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client
        Args:
            api_key: Google API key. If None, will look for GEMINI_API_KEY env var
        """
        if not GENAI_AVAILABLE:
            raise ValueError("google.genai or google.generativeai package not installed. Run: pip install google-generativeai")

        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable or pass as argument.")

        genai.configure(api_key=self.api_key)

        # Use Gemini Flash - fast and free tier available
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except AttributeError:
            # Fallback for older API
            self.model = genai.GenerativeModel('gemini-flash')

    def summarize_findings(self, findings_data: Dict[str, Any], customer_context=None) -> Dict[str, Any]:
        """
        Takes structured findings and generates executive summary + recommendations

        Args:
            findings_data: Output from RecommendationsEngine.analyze()

        Returns:
            Dict with:
                - executive_summary: 2-3 sentence overview
                - top_recommendations: List of prioritized actions
                - risks: List of key risks identified
                - next_steps: Concrete action items
                - quick_wins: Easy improvements with high impact
        """
        # Prepare a clean payload for Gemini (no PII, just metadata)
        clean_findings = self._prepare_clean_payload(findings_data)

        # Generate prompt (with optional customer context)
        prompt = self._build_prompt(clean_findings, customer_context)

        try:
            # Try using REST API directly to avoid SSL issues
            import requests

            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

            headers = {
                "Content-Type": "application/json"
            }

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json"
                }
            }

            response = requests.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}: {response.text}")

            data = response.json()

            # Extract text from response
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                result = json.loads(text)

                # Add metadata
                result['generated_by'] = 'gemini-2.0-flash-exp'
                result['workspace'] = findings_data.get('workspace', 'Unknown')
                result['analysis_date'] = findings_data.get('analysis_date')

                return result
            else:
                raise Exception("No candidates in response")

        except Exception as e:
            # Graceful fallback - return structured findings without AI summary
            print(f"Gemini API error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_summary(findings_data)

    def _prepare_clean_payload(self, findings_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strip PII and prepare minimal payload for Gemini
        Only send metadata and aggregates, no raw audience names or trait values
        """
        clean = {
            "workspace": findings_data.get('workspace', 'Customer'),
            "total_findings": findings_data.get('total_findings', 0),
            "high_priority": findings_data.get('high_priority', 0),
            "medium_priority": findings_data.get('medium_priority', 0),
            "low_priority": findings_data.get('low_priority', 0),
            "findings": []
        }

        # Include finding summaries but not full lists of affected items
        for finding in findings_data.get('findings', []):
            clean_finding = {
                "type": finding.get('type'),
                "severity": finding.get('severity'),
                "title": finding.get('title'),
                "evidence": finding.get('evidence'),
                "impact": finding.get('impact'),
                "recommendation": finding.get('recommendation'),
                "count": finding.get('count', 0)
            }
            # Do NOT include affected_items list to avoid sending audience names/trait names
            clean['findings'].append(clean_finding)

        return clean

    def _build_prompt(self, clean_findings: Dict[str, Any], customer_context=None) -> str:
        """Build prompt for Gemini using optimized prompt system"""
        try:
            from gemini_prompt_system import GeminiPromptSystem
            prompt_system = GeminiPromptSystem()
            return prompt_system.get_analysis_prompt(clean_findings, customer_context)
        except ImportError:
            # Fallback to simple prompt if prompt system not available
            return self._build_simple_prompt(clean_findings)

    def _build_simple_prompt(self, clean_findings: Dict[str, Any]) -> str:
        """Fallback simple prompt"""
        findings_json = json.dumps(clean_findings, indent=2)

        prompt = f"""You are an expert Customer Data Platform (CDP) consultant analyzing workspace health for a Segment customer.

Below is structured analysis data from an automated audit. Your task is to generate a concise, actionable summary.

**Input Data:**
```json
{findings_json}
```

**Your Task:**
Generate a JSON response with the following structure:

```json
{{
  "executive_summary": "2-3 sentence high-level overview of workspace health and key themes",
  "top_recommendations": [
    {{
      "priority": "high" | "medium" | "low",
      "action": "Specific action item",
      "reason": "Why this matters",
      "estimated_impact": "What improvement this will drive"
    }}
  ],
  "risks": [
    {{
      "risk": "Description of risk",
      "likelihood": "high" | "medium" | "low",
      "mitigation": "How to address"
    }}
  ],
  "quick_wins": [
    {{
      "action": "Easy-to-implement improvement",
      "effort": "low" | "medium",
      "impact": "Expected benefit"
    }}
  ],
  "next_steps": [
    "Concrete action item 1",
    "Concrete action item 2",
    "Concrete action item 3"
  ]
}}
```

**Guidelines:**
1. Focus on actionable insights, not just repeating the findings
2. Prioritize by business impact, not just severity
3. "Quick wins" should be low-effort, high-impact items
4. Keep language clear and non-technical where possible
5. Limit top_recommendations to 5 items maximum
6. Limit risks to 3-4 items maximum
7. Provide 3-5 next_steps as a prioritized checklist

Return ONLY valid JSON, no markdown formatting or explanation."""

        return prompt

    def _fallback_summary(self, findings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback summary if Gemini API fails"""
        findings = findings_data.get('findings', [])

        # Simple rule-based summary
        high = findings_data.get('high_priority', 0)
        medium = findings_data.get('medium_priority', 0)
        low = findings_data.get('low_priority', 0)

        summary = f"Found {len(findings)} total findings: {high} high priority, {medium} medium priority, {low} low priority."

        if high > 0:
            summary += " Immediate attention required for high-priority issues."

        # Extract top recommendations from findings
        top_recs = []
        for finding in findings[:5]:
            top_recs.append({
                "priority": finding.get('severity', 'medium'),
                "action": finding.get('title'),
                "reason": finding.get('impact'),
                "estimated_impact": finding.get('recommendation')
            })

        return {
            "executive_summary": summary,
            "top_recommendations": top_recs,
            "risks": [],
            "quick_wins": [],
            "next_steps": [
                "Review high-priority findings",
                "Prioritize quick wins",
                "Create action plan"
            ],
            "generated_by": "fallback",
            "workspace": findings_data.get('workspace'),
            "analysis_date": findings_data.get('analysis_date')
        }


def generate_ai_summary(findings_data: Dict[str, Any], api_key: Optional[str] = None, customer_context=None) -> Dict[str, Any]:
    """
    Main entry point - generate AI summary from findings

    Args:
        findings_data: Output from recommendations_engine.generate_recommendations()
        api_key: Optional Gemini API key (otherwise uses GEMINI_API_KEY env var)
        customer_context: Optional CustomerContext for tailored recommendations

    Returns:
        AI-generated summary with recommendations
    """
    try:
        summarizer = GeminiSummarizer(api_key=api_key)
        return summarizer.summarize_findings(findings_data, customer_context)
    except ValueError as e:
        # API key not configured - return fallback
        print(f"Gemini not configured: {e}")
        summarizer = GeminiSummarizer.__new__(GeminiSummarizer)
        return summarizer._fallback_summary(findings_data)


if __name__ == '__main__':
    # Test with sample findings
    from recommendations_engine import generate_recommendations

    print("Generating findings...")
    findings = generate_recommendations()

    print(f"\nFound {findings['total_findings']} findings")
    print(f"  High: {findings['high_priority']}")
    print(f"  Medium: {findings['medium_priority']}")
    print(f"  Low: {findings['low_priority']}")

    print("\nCalling Gemini API for summary...")
    summary = generate_ai_summary(findings)

    print("\n=== AI-GENERATED SUMMARY ===")
    print(json.dumps(summary, indent=2))
