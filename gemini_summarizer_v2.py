#!/usr/bin/env python3
"""
Gemini Summarizer V2 - Multi-layer prompting for high-quality, specific outputs
Implements: Summarization → Diagnosis → Opportunities → Execution pipeline
"""

import json
import os
from typing import Dict, Any, Optional
import requests
from data_structurer import DataStructurer
from multi_layer_prompts import MultiLayerPrompts


class GeminiSummarizerV2:
    """Multi-layer AI analysis using best practice prompting patterns"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key"""
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable")

        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        self.structurer = DataStructurer()
        self.prompts = MultiLayerPrompts()

    def analyze_workspace(self, findings_data: Dict[str, Any], multi_layer: bool = True) -> Dict[str, Any]:
        """
        Main entry point: Analyze workspace with multi-layer prompting

        Args:
            findings_data: Output from recommendations_engine
            multi_layer: If True, uses 4-layer approach; if False, single-pass

        Returns:
            Complete analysis with all layers
        """
        print("\n" + "="*70)
        print("🧠 GEMINI AI ANALYSIS")
        print("="*70)

        # Step 1: Structure data for LLM consumption
        print("📊 Step 1: Structuring data into curated context blocks...")
        structured_data = self.structurer.structure_for_gemini(findings_data)
        print(f"   ✓ Generated {len(json.dumps(structured_data))} chars of structured context")

        if not multi_layer:
            # Single-pass analysis (faster, less detailed)
            return self._single_pass_analysis(structured_data)

        # Multi-layer analysis (best quality)
        print("\n🔄 Step 2: Running multi-layer analysis...")

        # Layer 1: Summarization
        print("   Layer 1: Summarization (What's happening?)...")
        layer1_result = self._call_gemini(
            self.prompts.layer1_summarization(structured_data),
            system_instructions=self.prompts.get_system_instructions()
        )

        # Layer 2: Diagnosis
        print("   Layer 2: Diagnosis (What's wrong/missing?)...")
        layer2_result = self._call_gemini(
            self.prompts.layer2_diagnosis(structured_data),
            system_instructions=self.prompts.get_system_instructions()
        )

        # Layer 3: Opportunities
        print("   Layer 3: Opportunities (What could they do?)...")
        layer3_result = self._call_gemini(
            self.prompts.layer3_opportunities(structured_data),
            system_instructions=self.prompts.get_system_instructions()
        )

        # Layer 4: Execution Plan
        print("   Layer 4: Execution (What should they do next?)...")
        layer4_result = self._call_gemini(
            self.prompts.layer4_execution(structured_data, layer2_result, layer3_result),
            system_instructions=self.prompts.get_system_instructions()
        )

        # Combine all layers
        combined_result = {
            "meta": {
                "workspace": findings_data.get('workspace'),
                "analysis_type": "multi_layer",
                "layers_completed": 4
            },
            "layer1_summary": layer1_result,
            "layer2_diagnosis": layer2_result,
            "layer3_use_cases": layer3_result,
            "layer4_execution": layer4_result,
            "structured_data": structured_data  # Include for reference
        }

        print("\n✅ Analysis complete!")
        print("="*70 + "\n")

        return combined_result

    def _single_pass_analysis(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Single-pass analysis (faster but less detailed)"""
        print("   Using single-pass analysis...")

        prompt = f"""Analyze this Segment workspace and provide actionable recommendations.

### Workspace Data
```json
{json.dumps(structured_data, indent=2)}
```

Provide:
1. Executive summary (3 sentences)
2. Top 5 recommendations (specific, with names)
3. Quick wins (low effort, high impact)

Be specific - use actual audience names, destinations, and numbers.

Return JSON with: executive_summary, recommendations, quick_wins"""

        result = self._call_gemini(prompt, system_instructions=self.prompts.get_system_instructions())

        return {
            "meta": {"analysis_type": "single_pass"},
            "analysis": result,
            "structured_data": structured_data
        }

    def _call_gemini(self, prompt: str, system_instructions: str = "") -> Dict[str, Any]:
        """Call Gemini API via REST (avoids SSL issues)"""
        try:
            headers = {"Content-Type": "application/json"}

            # Build payload
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json"
                }
            }

            # Add system instructions if provided
            if system_instructions:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instructions}]
                }

            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=60  # Longer timeout for complex analysis
            )

            if response.status_code != 200:
                error_msg = f"Gemini API error {response.status_code}: {response.text}"
                print(f"   ❌ {error_msg}")
                return {"error": error_msg}

            data = response.json()

            # Extract JSON response
            if 'candidates' in data and len(data['candidates']) > 0:
                content = data['candidates'][0]['content']['parts'][0]['text']
                try:
                    # Parse JSON response
                    return json.loads(content)
                except json.JSONDecodeError:
                    # If not valid JSON, return as text
                    return {"raw_response": content}
            else:
                return {"error": "No response from Gemini"}

        except requests.exceptions.Timeout:
            return {"error": "Gemini API timeout - try again"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


def generate_ai_summary_v2(findings_data: Dict[str, Any], api_key: Optional[str] = None, multi_layer: bool = True) -> Dict[str, Any]:
    """
    Main entry point for generating AI-enhanced recommendations

    Args:
        findings_data: Output from recommendations_engine.generate_recommendations()
        api_key: Gemini API key (optional, will use env var if not provided)
        multi_layer: Use multi-layer prompting (True) or single-pass (False)

    Returns:
        Complete AI analysis
    """
    try:
        summarizer = GeminiSummarizerV2(api_key=api_key)
        return summarizer.analyze_workspace(findings_data, multi_layer=multi_layer)
    except ValueError as e:
        # API key missing
        return {
            "error": str(e),
            "fallback": "AI analysis unavailable - set GEMINI_API_KEY to enable"
        }
    except Exception as e:
        # Other errors
        return {
            "error": f"AI analysis failed: {str(e)}",
            "fallback": "Review rule-based findings for insights"
        }


# CLI testing
if __name__ == '__main__':
    import sys

    print("="*70)
    print("GEMINI SUMMARIZER V2 - Multi-Layer Analysis")
    print("="*70 + "\n")

    # Load findings
    from recommendations_engine import generate_recommendations
    findings = generate_recommendations()

    # Run analysis
    if len(sys.argv) > 1 and sys.argv[1] == '--single':
        print("Running SINGLE-PASS analysis...\n")
        result = generate_ai_summary_v2(findings, multi_layer=False)
    else:
        print("Running MULTI-LAYER analysis...\n")
        result = generate_ai_summary_v2(findings, multi_layer=True)

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(json.dumps(result, indent=2))
