#!/usr/bin/env python3
"""
Direct test of Gemini API for goal-driven prompts
Run: GEMINI_API_KEY=your_key python3 test_gemini_direct.py
"""

import os
import json
import re

# Set API key
os.environ['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', 'AIzaSyDvVcIeKWD3c0qzEteaVbvmKXWg1AAlNKU')

print("="*70)
print("TESTING GOAL-DRIVEN GEMINI FLOW")
print("="*70)

# Step 1: Generate findings
print("\n[1/6] Generating findings...")
from recommendations_engine import generate_recommendations
findings = generate_recommendations('./audit_data')
print(f"   ✓ {findings['total_findings']} findings generated")

# Step 2: Structure data
print("\n[2/6] Structuring data...")
from data_structurer import DataStructurer
structurer = DataStructurer('./audit_data')
structured_data = structurer.structure_for_gemini(findings)
print(f"   ✓ {structured_data['workspace_summary']['total_audiences']} audiences structured")
print(f"   ✓ {structured_data['workspace_summary']['total_users_in_audiences']:,} total users")

# Step 3: Business inference
print("\n[3/6] Inferring business context...")
from business_inference_prompts import BusinessInferencePrompts
import google.generativeai as genai

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.0-flash-exp')

layer0_prompt = BusinessInferencePrompts.get_business_inference_prompt(structured_data)
try:
    layer0_response = model.generate_content(layer0_prompt)
    layer0_result = json.loads(layer0_response.text)
    print(f"   ✓ Industry: {layer0_result['industry']['primary']}")
    print(f"   ✓ Business Model: {layer0_result.get('business_model', {}).get('primary', 'N/A')}")
except Exception as e:
    print(f"   ⚠️  Layer 0 failed: {e}")
    layer0_result = {
        'industry': {'primary': 'Media/Publishing'},
        'business_model': {'primary': 'Subscription'}
    }

# Step 4: Build context
print("\n[4/6] Building business context...")
business_context = f"""Industry: {layer0_result['industry']['primary']}
Business Model: {layer0_result.get('business_model', {}).get('primary', 'Unknown')}"""
user_notes = "This is Axios - digital media company with newsletters"
print(f"   ✓ Context ready")

# Step 5: Generate growth use cases prompt
print("\n[5/6] Generating growth use cases prompt...")
from goal_driven_prompts import GoalDrivenPrompts
prompts = GoalDrivenPrompts()
prompt = prompts.goal_growth_usecases(structured_data, business_context, user_notes)
print(f"   ✓ Prompt generated: {len(prompt):,} characters")

# Step 6: Call Gemini
print("\n[6/6] Calling Gemini API...")
print("   (This may take 10-30 seconds...)")
try:
    response = model.generate_content(prompt)
    response_text = response.text.strip()

    print(f"\n   ✓ Response received: {len(response_text):,} characters")

    # Try parsing JSON
    result = None
    try:
        result = json.loads(response_text)
        print(f"   ✓ Direct JSON parse successful!")
    except json.JSONDecodeError:
        # Try markdown extraction
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            result = json.loads(json_str)
            print(f"   ✓ Extracted JSON from markdown!")
        else:
            print(f"   ✗ No JSON found in response")
            print(f"\n   Response preview (first 1000 chars):")
            print("   " + "-"*66)
            print("   " + response_text[:1000])
            print("   " + "-"*66)

    if result:
        print(f"\n   Result keys: {list(result.keys())}")
        if 'use_cases' in result:
            print(f"   ✓ Generated {len(result['use_cases'])} use cases:")
            for i, uc in enumerate(result['use_cases'][:3], 1):
                print(f"      {i}. {uc.get('name', 'N/A')}")

            # Save result
            with open('/tmp/gemini_growth_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n   📄 Full result saved to: /tmp/gemini_growth_result.json")
        else:
            print(f"   ⚠️  No 'use_cases' key in result")
            print(f"\n   Full result:")
            print(json.dumps(result, indent=2)[:500])

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
