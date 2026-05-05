#!/usr/bin/env python3
"""
Customer Context System
Provides industry and use-case context for tailored recommendations
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Industry(Enum):
    """Common industry types"""
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    MEDIA = "media"
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    TRAVEL = "travel"
    EDUCATION = "education"
    GAMING = "gaming"
    B2B = "b2b"
    MARKETPLACE = "marketplace"
    UNKNOWN = "unknown"


class UseCase(Enum):
    """Primary Segment use cases"""
    MARKETING_AUTOMATION = "marketing_automation"
    PRODUCT_ANALYTICS = "product_analytics"
    PERSONALIZATION = "personalization"
    CUSTOMER_360 = "customer_360"
    LIFECYCLE_MARKETING = "lifecycle_marketing"
    ATTRIBUTION = "attribution"
    DATA_WAREHOUSE = "data_warehouse"
    UNKNOWN = "unknown"


@dataclass
class CustomerContext:
    """Customer-specific context for tailored recommendations"""

    # Basic info
    workspace_slug: str
    customer_name: Optional[str] = None

    # Business context
    industry: Industry = Industry.UNKNOWN
    use_case: UseCase = UseCase.UNKNOWN

    # Goals and priorities
    primary_goal: Optional[str] = None  # e.g., "increase newsletter engagement"
    secondary_goals: list = None  # e.g., ["reduce churn", "improve attribution"]

    # Tech stack
    key_destinations: list = None  # e.g., ["Braze", "Google Ads", "Snowflake"]
    current_challenges: list = None  # e.g., ["low activation rate", "poor data quality"]

    # Team context
    team_size: Optional[str] = None  # "small (<5)", "medium (5-20)", "large (20+)"
    technical_maturity: Optional[str] = None  # "beginner", "intermediate", "advanced"

    def __post_init__(self):
        if self.secondary_goals is None:
            self.secondary_goals = []
        if self.key_destinations is None:
            self.key_destinations = []
        if self.current_challenges is None:
            self.current_challenges = []

    def to_prompt_context(self) -> str:
        """Convert to natural language context for AI prompt"""
        parts = []

        # Industry and use case
        if self.industry != Industry.UNKNOWN:
            parts.append(f"Industry: {self.industry.value}")
        if self.use_case != UseCase.UNKNOWN:
            parts.append(f"Primary use case: {self.use_case.value}")

        # Goals
        if self.primary_goal:
            parts.append(f"Primary goal: {self.primary_goal}")
        if self.secondary_goals:
            parts.append(f"Secondary goals: {', '.join(self.secondary_goals)}")

        # Tech stack
        if self.key_destinations:
            parts.append(f"Key destinations: {', '.join(self.key_destinations)}")

        # Challenges
        if self.current_challenges:
            parts.append(f"Current challenges: {', '.join(self.current_challenges)}")

        # Team
        if self.team_size:
            parts.append(f"Team size: {self.team_size}")
        if self.technical_maturity:
            parts.append(f"Technical maturity: {self.technical_maturity}")

        if not parts:
            return "No specific customer context provided. Provide generic, universally applicable recommendations."

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "workspace_slug": self.workspace_slug,
            "customer_name": self.customer_name,
            "industry": self.industry.value,
            "use_case": self.use_case.value,
            "primary_goal": self.primary_goal,
            "secondary_goals": self.secondary_goals,
            "key_destinations": self.key_destinations,
            "current_challenges": self.current_challenges,
            "team_size": self.team_size,
            "technical_maturity": self.technical_maturity
        }


class CustomerContextLibrary:
    """Pre-configured contexts for known customers"""

    @staticmethod
    def get_context(workspace_slug: str) -> CustomerContext:
        """Get customer context by workspace slug"""

        # Known customers
        contexts = {
            "axios": CustomerContext(
                workspace_slug="axios",
                customer_name="Axios",
                industry=Industry.MEDIA,
                use_case=UseCase.LIFECYCLE_MARKETING,
                primary_goal="Increase newsletter engagement and subscriber retention",
                secondary_goals=["Improve content personalization", "Reduce unsubscribe rate"],
                key_destinations=["Braze", "Iterable", "Snowflake"],
                team_size="medium (5-20)",
                technical_maturity="intermediate"
            ),
            # Add more as needed
        }

        # Return known context or generic
        return contexts.get(workspace_slug, CustomerContext(workspace_slug=workspace_slug))

    @staticmethod
    def create_generic_context(workspace_slug: str) -> CustomerContext:
        """Create a generic context for unknown customers"""
        return CustomerContext(
            workspace_slug=workspace_slug,
            industry=Industry.UNKNOWN,
            use_case=UseCase.UNKNOWN
        )


class ContextualRecommendations:
    """Generate use-case specific recommendations based on customer context"""

    @staticmethod
    def get_industry_guidance(industry: Industry) -> Dict[str, Any]:
        """Get industry-specific best practices"""

        guidance = {
            Industry.SAAS: {
                "key_events": ["trial_started", "feature_used", "upgrade_completed", "user_invited"],
                "key_audiences": ["trial_users", "power_users", "at_risk_churners", "expansion_candidates"],
                "activation_priorities": ["Product analytics", "Lifecycle emails", "In-app messaging"],
                "typical_challenges": ["Product-led growth tracking", "Feature adoption", "Expansion revenue"]
            },
            Industry.ECOMMERCE: {
                "key_events": ["product_viewed", "cart_added", "checkout_started", "order_completed"],
                "key_audiences": ["cart_abandoners", "high_ltv_customers", "first_time_buyers", "repeat_purchasers"],
                "activation_priorities": ["Email/SMS remarketing", "Paid media retargeting", "On-site personalization"],
                "typical_challenges": ["Cart abandonment", "Customer retention", "Attribution"]
            },
            Industry.MEDIA: {
                "key_events": ["article_viewed", "newsletter_opened", "subscription_started", "video_played"],
                "key_audiences": ["engaged_readers", "subscribers", "potential_churners", "free_to_paid_prospects"],
                "activation_priorities": ["Email campaigns", "Content recommendations", "Subscription prompts"],
                "typical_challenges": ["Engagement metrics", "Subscription conversion", "Churn prevention"]
            },
            Industry.FINTECH: {
                "key_events": ["account_opened", "transaction_completed", "deposit_made", "feature_activated"],
                "key_audiences": ["new_users", "active_traders", "dormant_accounts", "high_balance_users"],
                "activation_priorities": ["Compliance-safe messaging", "Security alerts", "Product education"],
                "typical_challenges": ["Regulatory compliance", "Fraud detection", "Customer trust"]
            },
            Industry.B2B: {
                "key_events": ["demo_requested", "trial_started", "meeting_scheduled", "contract_signed"],
                "key_audiences": ["qualified_leads", "trial_users", "decision_makers", "expansion_accounts"],
                "activation_priorities": ["Sales automation", "Account-based marketing", "Customer success"],
                "typical_challenges": ["Long sales cycles", "Multi-stakeholder decisions", "Account expansion"]
            }
        }

        return guidance.get(industry, {
            "key_events": [],
            "key_audiences": [],
            "activation_priorities": ["Email marketing", "Analytics", "Personalization"],
            "typical_challenges": []
        })

    @staticmethod
    def get_use_case_guidance(use_case: UseCase) -> Dict[str, Any]:
        """Get use-case specific recommendations"""

        guidance = {
            UseCase.MARKETING_AUTOMATION: {
                "focus": "Audience activation and campaign orchestration",
                "critical_destinations": ["Braze", "Iterable", "Customer.io", "Klaviyo"],
                "key_metrics": ["Activation rate", "Campaign engagement", "Conversion lift"],
                "common_issues": ["Audiences not synced", "Stale segments", "Low activation rate"]
            },
            UseCase.PRODUCT_ANALYTICS: {
                "focus": "Event tracking and behavioral analysis",
                "critical_destinations": ["Amplitude", "Mixpanel", "Heap"],
                "key_metrics": ["Event volume", "Feature adoption", "Retention cohorts"],
                "common_issues": ["Inconsistent naming", "Missing properties", "Low event coverage"]
            },
            UseCase.PERSONALIZATION: {
                "focus": "Real-time audience membership and content targeting",
                "critical_destinations": ["Optimizely", "Dynamic Yield", "AB Tasty"],
                "key_metrics": ["Segment coverage", "Sync latency", "Personalization lift"],
                "common_issues": ["Slow sync times", "Limited trait usage", "Static segments"]
            },
            UseCase.CUSTOMER_360: {
                "focus": "Unified customer view across touchpoints",
                "critical_destinations": ["Snowflake", "BigQuery", "Salesforce"],
                "key_metrics": ["Identity resolution rate", "Profile completeness", "Data freshness"],
                "common_issues": ["Anonymous users", "Fragmented identities", "Missing traits"]
            }
        }

        return guidance.get(use_case, {
            "focus": "General data collection and activation",
            "critical_destinations": [],
            "key_metrics": [],
            "common_issues": []
        })


def get_contextual_prompt_section(context: CustomerContext) -> str:
    """Generate prompt section with customer context"""

    if context.industry == Industry.UNKNOWN and context.use_case == UseCase.UNKNOWN:
        return """
### Customer Context
No specific customer context provided. Generate recommendations that are:
- Universally applicable across industries
- Focused on tactical improvements (data quality, activation gaps, hygiene)
- Not assuming specific business models or use cases
- Prioritized by common patterns (high-volume = important, zero-users = delete, etc.)
"""

    # Get industry and use case guidance
    industry_guide = ContextualRecommendations.get_industry_guidance(context.industry)
    use_case_guide = ContextualRecommendations.get_use_case_guidance(context.use_case)

    prompt = f"""
### Customer Context
{context.to_prompt_context()}

### Industry Context ({context.industry.value})
Typical key events: {', '.join(industry_guide.get('key_events', [])[:5])}
Typical audiences: {', '.join(industry_guide.get('key_audiences', [])[:5])}
Activation priorities: {', '.join(industry_guide.get('activation_priorities', []))}
Common challenges: {', '.join(industry_guide.get('typical_challenges', []))}

### Use Case Context ({context.use_case.value})
Focus area: {use_case_guide.get('focus', 'Unknown')}
Critical destinations: {', '.join(use_case_guide.get('critical_destinations', [])[:5])}
Key metrics: {', '.join(use_case_guide.get('key_metrics', []))}

### Recommendation Guidelines
- Prioritize actions that support: {context.primary_goal or 'general workspace health'}
- Tailor recommendations to {context.industry.value} industry patterns
- Consider team capacity: {context.team_size or 'unknown team size'}
- Match technical level: {context.technical_maturity or 'unknown maturity'}
"""

    return prompt


# Example usage
if __name__ == '__main__':
    # Test with Axios
    axios_context = CustomerContextLibrary.get_context("axios")
    print("=== AXIOS CONTEXT ===")
    print(axios_context.to_prompt_context())
    print()

    # Test with generic customer
    generic_context = CustomerContextLibrary.get_context("unknown-customer")
    print("=== GENERIC CONTEXT ===")
    print(generic_context.to_prompt_context())
    print()

    # Test contextual prompt
    print("=== CONTEXTUAL PROMPT FOR AXIOS ===")
    print(get_contextual_prompt_section(axios_context))
