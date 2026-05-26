#!/usr/bin/env python3
"""
Business Inference Prompts - Infer business context from data patterns
Layer 0 of multi-layer analysis: Understand WHO the customer is before analyzing
"""

import json
from typing import Dict, Any


class BusinessInferencePrompts:
    """
    Prompts for inferring business context from workspace data patterns
    This is the critical first step: Know the customer before recommending
    """

    @staticmethod
    def get_inference_system_instructions() -> str:
        """System instructions for business inference"""
        return """You are a CDP Solutions Architect with deep expertise in:
- Pattern recognition across industries (e-commerce, SaaS, media, fintech, marketplace, B2B)
- Business model identification (subscription, transactional, ad-based, lead-gen, marketplace)
- User behavior analysis from event patterns
- Conversion funnel identification

Your task: Infer business context ONLY from data patterns.

Critical rules:
- Base reasoning ONLY on patterns in the data provided
- Do NOT hallucinate or assume information not present
- If uncertain, mark confidence as "low" and explain why
- If multiple patterns exist, explain the business model mix
- Provide reasoning for each inference (show your work)"""

    @staticmethod
    def get_business_inference_prompt(structured_data: Dict[str, Any]) -> str:
        """
        Layer 0: Infer business context from data patterns

        This prompt analyzes:
        - Event names and patterns
        - Audience names and categories
        - Destination types
        - User behavior signals

        Returns inferred business context with confidence scores
        """

        # Extract key patterns for analysis
        audiences = structured_data.get('audience_insights', [])
        sources = structured_data.get('source_insights', [])
        destinations = structured_data.get('destination_summary', {})

        # Build pattern summary for analysis
        audience_names = [a.get('name', '') for a in audiences[:30]]
        audience_categories = {}
        for a in audiences:
            cat = a.get('category', 'general')
            audience_categories[cat] = audience_categories.get(cat, 0) + 1

        destination_list = destinations.get('all_destinations', [])
        dest_by_category = destinations.get('by_category', {})

        return f"""## Business Context Inference

You are analyzing a Segment workspace to understand the customer's business.

### Data Patterns Available

**Audience Names (sample of {len(audience_names)}):**
```
{chr(10).join(audience_names[:20])}
```

**Audience Category Distribution:**
```json
{json.dumps(audience_categories, indent=2)}
```

**Destinations Connected:**
```json
{json.dumps(destination_list, indent=2)}
```

**Destination Categories:**
```json
{json.dumps(dest_by_category, indent=2)}
```

**Source Types:**
- Total sources: {len(sources)}
- Enabled: {len([s for s in sources if s.get('signal') == 'healthy'])}

---

## Task: Infer Business Context

Analyze the patterns above and infer:

### 1. Industry Classification

Use these heuristics:

**E-commerce Signals:**
- Event patterns: "Order", "Checkout", "Product", "Cart", "Purchase", "Payment"
- Audience patterns: "cart_abandoners", "high_ltv", "first_time_buyers"
- Destinations: Klaviyo, Facebook Ads, Google Ads, Attentive

**SaaS/Subscription Signals:**
- Event patterns: "Subscription", "Plan", "Upgrade", "Trial", "Feature", "Login"
- Audience patterns: "trial_users", "churned", "power_users", "plan_tier"
- Destinations: Intercom, Amplitude, Mixpanel, Customer.io

**Media/Publishing Signals:**
- Event patterns: "Article", "Read", "Newsletter", "Content", "View", "Engagement"
- Audience patterns: "subscribers", "readers", "engaged", "newsletter_*"
- Destinations: Braze, Iterable, Piano, Sailthru

**Marketplace Signals:**
- Event patterns: "Booking", "Ride", "Listing", "Host", "Guest", "Request"
- Audience patterns: "buyers", "sellers", "hosts", "service_providers"
- Destinations: Braze, Amplitude, mParticle

**B2B/Lead-Gen Signals:**
- Event patterns: "Lead", "Demo", "Form", "MQL", "SQL", "Opportunity"
- Audience patterns: "leads", "qualified", "enterprise", "accounts"
- Destinations: Salesforce, Marketo, HubSpot, Clearbit

**Fintech Signals:**
- Event patterns: "Transaction", "Transfer", "Balance", "Account", "KYC"
- Audience patterns: "verified", "high_balance", "active_traders"
- Destinations: Amplitude, Braze, fraud detection tools

Based on the data patterns, determine:

**Primary Industry:** [industry name]
**Confidence:** high | medium | low
**Reasoning:** [explain which patterns led to this conclusion]

**Secondary Industry (if applicable):** [industry name or null]
**Reasoning:** [explain mixed signals if present]

### 2. Business Model Classification

**Subscription Model Signals:**
- Audience patterns: "trial", "subscriber", "plan", "tier", "churned"
- Event patterns: "subscription_started", "plan_upgraded", "billing"

**Transactional Model Signals:**
- Audience patterns: "purchaser", "order", "transaction"
- Event patterns: "checkout", "order_completed", "payment"

**Ad-Based Model Signals:**
- Audience patterns: "engaged", "session", "page_views"
- Event patterns: "ad_viewed", "impression", "click"
- Destinations: Ad platforms (Google Ads, Facebook Ads, etc.)

**Lead-Gen Model Signals:**
- Audience patterns: "lead", "mql", "sql", "demo_requested"
- Event patterns: "form_submitted", "demo_booked"

**Marketplace Model Signals:**
- Audience patterns: "buyer", "seller", "host", "provider"
- Event patterns: "listing_created", "booking_made"

Based on the data patterns, determine:

**Primary Business Model:** [model name]
**Confidence:** high | medium | low
**Reasoning:** [explain evidence]

**Secondary Model (if applicable):** [model name or null]

### 3. Primary User Behaviors

Infer the main user actions based on audience categories and naming patterns.

Examples:
- If many "subscriber" audiences → "newsletter consumption, content engagement"
- If many "trial" audiences → "product evaluation, feature discovery"
- If many "cart" audiences → "shopping, purchasing"

**Primary Behaviors:** [list 3-5 key behaviors]
**Confidence:** high | medium | low
**Evidence:** [which patterns indicate these behaviors]

### 4. Likely Conversion Events

Based on business model and audience patterns, infer what "conversion" likely means.

Examples:
- E-commerce: "order_completed", "purchase"
- SaaS: "subscription_started", "trial_converted"
- Media: "subscription_activated", "newsletter_subscribed"
- B2B: "demo_booked", "contract_signed"

**Primary Conversion Events:** [list 2-3 likely conversion events]
**Confidence:** high | medium | low
**Reasoning:** [explain inference]

### 5. Confidence Assessment

Overall confidence in inference:

**Overall Confidence:** high | medium | low

**Reasoning:**
- High: Strong, consistent signals across multiple data points
- Medium: Some signals present but limited data or mixed patterns
- Low: Insufficient data or contradictory patterns

**Data Quality Notes:** [any limitations or gaps in the data]

---

## Output Format

Return ONLY valid JSON with this structure:

```json
{{
  "industry": {{
    "primary": "industry name",
    "primary_confidence": "high | medium | low",
    "primary_reasoning": "explanation with specific evidence",
    "secondary": "industry name or null",
    "secondary_reasoning": "explanation if mixed signals"
  }},
  "business_model": {{
    "primary": "model name",
    "primary_confidence": "high | medium | low",
    "primary_reasoning": "evidence from data",
    "secondary": "model name or null",
    "revenue_model_notes": "additional context"
  }},
  "user_behaviors": {{
    "primary_behaviors": ["behavior 1", "behavior 2", "behavior 3"],
    "confidence": "high | medium | low",
    "evidence": "which data patterns support this"
  }},
  "conversion_events": {{
    "likely_conversions": ["event 1", "event 2"],
    "confidence": "high | medium | low",
    "reasoning": "why these are likely conversions"
  }},
  "overall_assessment": {{
    "confidence": "high | medium | low",
    "data_quality": "assessment of available data",
    "key_signals_found": ["signal 1", "signal 2"],
    "missing_signals": ["what would help increase confidence"],
    "business_summary": "1-2 sentence summary of inferred business"
  }}
}}
```

---

## Critical Guidelines

1. **Evidence-Based**: Every inference must cite specific patterns from the data
2. **Confidence Scoring**: Be honest about uncertainty - "low" confidence is valid
3. **No Hallucination**: Do not invent events, audiences, or patterns not in the data
4. **Explain Mixed Signals**: If data suggests multiple industries/models, explain both
5. **Show Your Work**: Include reasoning for each inference

---

## Example Inference (for reference)

If data shows:
- Audiences: "subscribers_axios_am", "newsletter_engaged", "local_va_subs"
- Destinations: Braze, Iterable, Sailthru
- Categories: Heavy "subscription" pattern

Then infer:
```json
{{
  "industry": {{
    "primary": "Media/Publishing",
    "primary_confidence": "high",
    "primary_reasoning": "Strong newsletter/subscriber patterns in audience names (subscribers_axios_am, newsletter_engaged). Email-focused destinations (Braze, Iterable, Sailthru) typical of media companies. Geographic audiences (local_va_subs) suggest news/media organization.",
    "secondary": null
  }},
  "business_model": {{
    "primary": "Subscription",
    "primary_confidence": "high",
    "primary_reasoning": "Heavy emphasis on subscriber audiences, newsletter engagement tracking. Email platform destinations for subscriber communication."
  }}
}}
```

Now analyze the provided data and return your inference."""

    @staticmethod
    def get_context_enrichment_prompt(inference_result: Dict[str, Any]) -> str:
        """
        Generate prompt additions based on inferred business context
        This enriches downstream layers with context-aware guidance
        """
        industry = inference_result.get('industry', {}).get('primary', 'Unknown')
        business_model = inference_result.get('business_model', {}).get('primary', 'Unknown')
        confidence = inference_result.get('overall_assessment', {}).get('confidence', 'low')

        context_guidance = f"""
---

## Inferred Business Context (Use this to tailor recommendations)

**Industry:** {industry} (confidence: {confidence})
**Business Model:** {business_model}

"""

        # Add industry-specific guidance
        if industry == "Media/Publishing":
            context_guidance += """
### Media/Publishing Best Practices

Key priorities:
1. Subscriber engagement and retention
2. Content personalization by topic/geography
3. Newsletter optimization (open rates, click-through)
4. Churn prevention through engagement scoring

Typical high-value audiences:
- Engaged subscribers (regular readers)
- At-risk subscribers (declining engagement)
- Geographic segments (for localized content)
- Topic affinity segments (for personalization)

Key destinations to recommend:
- Email platforms: Braze, Iterable, Customer.io
- Analytics: Amplitude, Mixpanel (for engagement tracking)
- Ad platforms: Only for acquisition/lookalike targeting

Campaign patterns:
- Re-engagement campaigns for inactive readers
- Geo-targeted content for regional audiences
- Topic-based personalization
- Subscriber milestone campaigns
"""

        elif industry == "SaaS":
            context_guidance += """
### SaaS/Subscription Best Practices

Key priorities:
1. Trial-to-paid conversion
2. Feature adoption and onboarding
3. Expansion revenue (upsells, cross-sells)
4. Churn prediction and prevention

Typical high-value audiences:
- Trial users (by activation level)
- Power users (for upsell)
- At-risk accounts (for retention)
- Feature-specific segments

Key destinations to recommend:
- Product analytics: Amplitude, Mixpanel, Heap
- Customer communication: Intercom, Customer.io
- Sales automation: Salesforce, HubSpot
- Ad platforms: For lookalike targeting

Campaign patterns:
- Onboarding sequences by feature usage
- Upsell campaigns to power users
- Win-back campaigns for churned users
- NPS surveys to promoters
"""

        elif industry == "E-commerce":
            context_guidance += """
### E-commerce Best Practices

Key priorities:
1. Cart abandonment recovery
2. Customer LTV maximization
3. Product recommendations
4. Win-back campaigns

Typical high-value audiences:
- Cart abandoners (by cart value)
- High LTV customers
- First-time buyers
- Product affinity segments

Key destinations to recommend:
- Email/SMS: Klaviyo, Attentive, Braze
- Ad platforms: Facebook Ads, Google Ads
- Personalization: Dynamic Yield, Nosto

Campaign patterns:
- Abandoned cart recovery (1hr, 24hr, 7day)
- Post-purchase cross-sell
- VIP program for high LTV
- Browse abandonment retargeting
"""

        elif industry == "B2B":
            context_guidance += """
### B2B/Lead-Gen Best Practices

Key priorities:
1. Lead qualification and scoring
2. Account-based marketing
3. Demo-to-close conversion
4. Multi-touch attribution

Typical high-value audiences:
- MQLs by source and engagement
- Enterprise accounts
- Demo requesters
- Product-qualified leads (PQLs)

Key destinations to recommend:
- CRM: Salesforce, HubSpot
- Marketing automation: Marketo, Pardot
- ABM platforms: Demandbase, 6sense
- Analytics: Amplitude for product usage

Campaign patterns:
- Lead nurturing by stage
- Account-based outreach
- Product education for trials
- Executive touchpoints for enterprise
"""

        else:
            # Generic guidance if industry unknown
            context_guidance += """
### General CDP Best Practices

Since industry is unclear, focus on universal recommendations:
1. Activate large, unconnected audiences
2. Build event-based behavioral segments
3. Connect to appropriate destination categories
4. Clean up stale/empty audiences
"""

        return context_guidance


# CLI testing
if __name__ == '__main__':
    print("=== BUSINESS INFERENCE PROMPT SYSTEM ===\n")

    # Sample data
    sample_data = {
        "audience_insights": [
            {"name": "subscribers_axios_am", "category": "subscription", "size": 100000},
            {"name": "newsletter_engaged", "category": "engagement", "size": 50000},
            {"name": "local_va_subs", "category": "geographic", "size": 20000}
        ],
        "destination_summary": {
            "all_destinations": ["Braze", "Iterable", "Sailthru"],
            "by_category": {
                "email": ["Braze", "Iterable", "Sailthru"]
            }
        }
    }

    prompt = BusinessInferencePrompts.get_business_inference_prompt(sample_data)
    print(f"Prompt length: {len(prompt)} characters")
    print("\nFirst 500 chars:")
    print(prompt[:500])
