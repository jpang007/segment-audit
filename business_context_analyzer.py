#!/usr/bin/env python3
"""
Business Context Analyzer - Infers business model and use cases from actual data
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import Counter


class BusinessContextAnalyzer:
    """Analyzes workspace data to infer business model and recommend use cases"""

    def __init__(self, audit_data_dir: str = './audit_data'):
        self.data_dir = Path(audit_data_dir)

    def analyze_business_context(self) -> Dict[str, Any]:
        """
        Analyze workspace to infer business model and opportunities
        Returns context including likely industry, use cases, and recommendations
        """
        context = {
            'likely_industries': [],
            'business_signals': {},
            'audience_patterns': {},
            'source_patterns': {},
            'event_patterns': {},
            'use_case_opportunities': []
        }

        # Analyze sources (CRITICAL for industry detection)
        sources = self._load_sources()
        if sources:
            context['source_patterns'] = self._analyze_source_patterns(sources)
            context['business_signals']['source_based'] = self._infer_from_sources(sources)

        # Analyze audiences
        audiences = self._load_audiences()
        if audiences:
            context['audience_patterns'] = self._analyze_audience_patterns(audiences)
            context['business_signals']['audience_based'] = self._infer_from_audiences(audiences)

        # Analyze events (if available)
        events = self._load_events()
        if events:
            context['event_patterns'] = self._analyze_event_patterns(events)
            context['business_signals']['event_based'] = self._infer_from_events(events)

        # Infer likely industries
        context['likely_industries'] = self._infer_industries(context)

        # Generate use case recommendations
        context['use_case_opportunities'] = self._generate_use_case_recommendations(
            audiences, events, context['likely_industries']
        )

        return context

    def _load_sources(self) -> List[Dict[str, str]]:
        """Load source data from Gateway API"""
        sources_file = self.data_dir / 'gateway_sources.csv'

        if not sources_file.exists():
            print("⚠️  WARNING: gateway_sources.csv not found")
            return []

        sources = []
        with open(sources_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sources.append(row)
        print(f"✓ Business analyzer loaded {len(sources)} sources from Gateway API")
        return sources

    def _load_audiences(self) -> List[Dict[str, str]]:
        """Load audience data from Gateway API ONLY"""
        audiences_file = self.data_dir / 'gateway_audiences.csv'

        if not audiences_file.exists():
            print("⚠️  WARNING: gateway_audiences.csv not found - using Gateway API files only")
            return []

        audiences = []
        with open(audiences_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                audiences.append(row)
        print(f"✓ Business analyzer loaded {len(audiences)} audiences from Gateway API")
        return audiences

    def _load_events(self) -> List[str]:
        """Load event names from event coverage or other sources"""
        events = []

        # Try event coverage
        event_file = self.data_dir / 'event_coverage.csv'
        if event_file.exists():
            with open(event_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    event_name = row.get('Event', '').strip()
                    if event_name:
                        events.append(event_name)

        return events

    def _analyze_audience_patterns(self, audiences: List[Dict]) -> Dict[str, Any]:
        """Analyze audience naming patterns and characteristics"""
        patterns = {
            'total_audiences': len(audiences),
            'enabled_count': 0,
            'with_users': 0,
            'themes': Counter(),
            'folders': Counter(),
            'size_distribution': {'small': 0, 'medium': 0, 'large': 0, 'empty': 0}
        }

        # Keywords indicating business models
        keywords = {
            'newsletter': 0, 'subscriber': 0, 'subscription': 0,
            'trial': 0, 'pro': 0, 'premium': 0, 'free': 0,
            'cart': 0, 'order': 0, 'purchase': 0, 'checkout': 0,
            'engagement': 0, 'active': 0, 'inactive': 0, 'churn': 0,
            'local': 0, 'national': 0, 'geo': 0,
            'deal': 0, 'vertical': 0, 'segment': 0,
            'test': 0, 'example': 0, 'suppression': 0, 'opt-out': 0,
            'dealer': 0, 'auction': 0, 'vehicle': 0, 'auto': 0, 'car': 0,
            'marketplace': 0, 'seller': 0, 'buyer': 0, 'listing': 0,
            'consignor': 0, 'bidder': 0, 'inventory': 0
        }

        for aud in audiences:
            name = aud.get('Name', '').lower()
            enabled = aud.get('Enabled', '').lower() == 'true'
            size_str = aud.get('Size', '0')
            folder = aud.get('Folder', '')

            if enabled:
                patterns['enabled_count'] += 1

            # Parse size
            try:
                size = int(size_str.replace(',', '')) if size_str and size_str != 'Computing...' else 0
            except (ValueError, AttributeError):
                size = 0

            if size > 0:
                patterns['with_users'] += 1
                if size < 1000:
                    patterns['size_distribution']['small'] += 1
                elif size < 100000:
                    patterns['size_distribution']['medium'] += 1
                else:
                    patterns['size_distribution']['large'] += 1
            else:
                patterns['size_distribution']['empty'] += 1

            # Track folder usage
            if folder:
                patterns['folders'][folder] += 1

            # Count keyword occurrences
            for keyword in keywords:
                if keyword in name:
                    keywords[keyword] += 1

        patterns['themes'] = dict(keywords)
        return patterns

    def _analyze_source_patterns(self, sources: List[Dict]) -> Dict[str, Any]:
        """Analyze source naming patterns - CRITICAL for industry detection"""
        patterns = {
            'total_sources': len(sources),
            'enabled_count': 0,
            'themes': Counter()
        }

        # Source name keywords for industry detection
        keywords = {
            'dealer': 0, 'auction': 0, 'vehicle': 0, 'auto': 0, 'car': 0,
            'marketplace': 0, 'seller': 0, 'buyer': 0, 'listing': 0,
            'consignor': 0, 'bidder': 0, 'inventory': 0,
            'newsletter': 0, 'subscriber': 0, 'subscription': 0,
            'ecommerce': 0, 'shop': 0, 'store': 0, 'cart': 0,
            'fintech': 0, 'payment': 0, 'banking': 0, 'finance': 0
        }

        for src in sources:
            name = src.get('Name', '').lower()
            status = src.get('Status', '')

            if status == 'ENABLED':
                patterns['enabled_count'] += 1

            # Count keyword occurrences in source names
            for keyword in keywords:
                if keyword in name:
                    keywords[keyword] += 1

        patterns['themes'] = dict(keywords)
        return patterns

    def _infer_from_sources(self, sources: List[Dict]) -> List[str]:
        """Infer business characteristics from source names - MOST RELIABLE signal"""
        signals = []

        themes = Counter()
        for src in sources:
            name = src.get('Name', '').lower()

            # Automotive/Marketplace signals (highest priority - very specific)
            if any(word in name for word in ['dealer', 'auction', 'vehicle', 'auto', 'car', 'consignor', 'bidder', 'autoniq']):
                themes['automotive_marketplace'] += 3  # Strong signal

            # Marketplace platform
            if 'marketplace' in name or 'seller' in name or 'buyer' in name or 'listing' in name:
                themes['marketplace_platform'] += 2

            # Media/Publishing
            if 'newsletter' in name or 'subscriber' in name or 'publication' in name:
                themes['newsletter_focused'] += 1

            # eCommerce
            if any(word in name for word in ['shop', 'store', 'cart', 'ecommerce', 'checkout']):
                themes['ecommerce'] += 1

        # Convert top themes to signals
        for theme, count in themes.most_common(5):
            if count >= 2:  # At least 2 sources with this theme (lowered threshold for sources)
                signals.append(theme)

        return signals

    def _analyze_event_patterns(self, events: List[str]) -> Dict[str, Any]:
        """Analyze event naming patterns"""
        patterns = {
            'total_events': len(events),
            'themes': Counter()
        }

        keywords = {
            'newsletter': 0, 'email': 0, 'open': 0, 'click': 0, 'send': 0,
            'article': 0, 'content': 0, 'view': 0, 'page': 0, 'read': 0,
            'subscription': 0, 'subscribe': 0, 'unsubscribe': 0,
            'purchase': 0, 'order': 0, 'cart': 0, 'checkout': 0,
            'signup': 0, 'login': 0, 'register': 0,
            'trial': 0, 'upgrade': 0, 'downgrade': 0,
            'payment': 0, 'billing': 0, 'invoice': 0,
            'auction': 0, 'bid': 0, 'vehicle': 0, 'dealer': 0, 'listing': 0,
            'marketplace': 0, 'seller': 0, 'buyer': 0, 'inventory': 0
        }

        for event in events:
            event_lower = event.lower()
            for keyword in keywords:
                if keyword in event_lower:
                    keywords[keyword] += 1

        patterns['themes'] = dict(keywords)
        return patterns

    def _infer_from_audiences(self, audiences: List[Dict]) -> List[str]:
        """Infer business characteristics from audience names"""
        signals = []

        # Count theme occurrences
        themes = Counter()
        for aud in audiences:
            name = aud.get('Name', '').lower()

            if 'newsletter' in name or 'subscriber' in name:
                themes['newsletter_focused'] += 1
            if 'pro' in name or 'premium' in name or 'subscription' in name:
                themes['subscription_business'] += 1
            if 'cart' in name or 'order' in name or 'purchase' in name:
                themes['ecommerce'] += 1
            if 'trial' in name or 'signup' in name:
                themes['saas_funnel'] += 1
            if 'local' in name or 'geo' in name or 'national' in name:
                themes['location_based'] += 1
            if 'engagement' in name or 'active' in name or 'churn' in name:
                themes['retention_focused'] += 1
            if 'deal' in name or 'vertical' in name:
                themes['b2b_segments'] += 1
            if any(word in name for word in ['dealer', 'auction', 'vehicle', 'auto', 'car', 'consignor', 'bidder', 'marketplace', 'inventory']):
                themes['automotive_marketplace'] += 1
            if 'marketplace' in name or 'seller' in name or 'buyer' in name or 'listing' in name:
                themes['marketplace_platform'] += 1

        # Convert top themes to signals
        for theme, count in themes.most_common(5):
            if count >= 3:  # At least 3 audiences with this theme
                signals.append(theme)

        return signals

    def _infer_from_events(self, events: List[str]) -> List[str]:
        """Infer business characteristics from event names"""
        signals = []

        themes = Counter()
        for event in events:
            event_lower = event.lower()

            if 'newsletter' in event_lower or 'email' in event_lower:
                themes['email_marketing'] += 1
            if 'article' in event_lower or 'content' in event_lower or 'read' in event_lower:
                themes['content_platform'] += 1
            if 'purchase' in event_lower or 'order' in event_lower or 'cart' in event_lower:
                themes['ecommerce'] += 1
            if 'subscription' in event_lower or 'subscribe' in event_lower:
                themes['subscription_model'] += 1
            if 'trial' in event_lower or 'signup' in event_lower:
                themes['freemium_saas'] += 1
            if any(word in event_lower for word in ['auction', 'bid', 'vehicle', 'dealer', 'listing', 'inventory']):
                themes['automotive_marketplace'] += 1
            if 'marketplace' in event_lower or 'seller' in event_lower or 'buyer' in event_lower:
                themes['marketplace_platform'] += 1

        for theme, count in themes.most_common(5):
            if count >= 2:
                signals.append(theme)

        return signals

    def _infer_industries(self, context: Dict) -> List[str]:
        """Infer likely industries from combined signals - SOURCE signals are most reliable"""
        industries = []

        source_signals = context['business_signals'].get('source_based', [])
        audience_signals = context['business_signals'].get('audience_based', [])
        event_signals = context['business_signals'].get('event_based', [])

        # Prioritize source signals (most reliable), then audience, then events
        all_signals = source_signals + audience_signals + event_signals

        # Media/Publishing
        media_indicators = ['newsletter_focused', 'email_marketing', 'content_platform', 'subscription_business']
        if any(sig in all_signals for sig in media_indicators):
            industries.append('Media/Publishing')

        # SaaS
        saas_indicators = ['saas_funnel', 'trial', 'freemium_saas', 'subscription_business']
        if any(sig in all_signals for sig in saas_indicators):
            industries.append('SaaS')

        # eCommerce
        ecommerce_indicators = ['ecommerce']
        if any(sig in all_signals for sig in ecommerce_indicators):
            industries.append('eCommerce')

        # B2B
        b2b_indicators = ['b2b_segments', 'vertical']
        if any(sig in all_signals for sig in b2b_indicators):
            industries.append('B2B')

        # Automotive/Marketplace
        automotive_indicators = ['automotive_marketplace']
        if any(sig in all_signals for sig in automotive_indicators):
            industries.append('Automotive/Marketplace')

        # Marketplace Platform
        marketplace_indicators = ['marketplace_platform']
        if any(sig in all_signals for sig in marketplace_indicators):
            if 'Automotive/Marketplace' not in industries:
                industries.append('Marketplace')

        # Default if nothing detected
        if not industries:
            industries.append('General')

        return industries

    def _generate_use_case_recommendations(
        self,
        audiences: List[Dict],
        events: List[str],
        industries: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate specific use case recommendations based on actual data"""
        recommendations = []

        # Analyze what they have vs what they could do
        enabled_audiences = [a for a in audiences if a.get('Enabled', '').lower() == 'true']
        audiences_with_destinations = [
            a for a in enabled_audiences
            if int(a.get('Destination Count', '0')) > 0
        ]
        audiences_without_destinations = [
            a for a in enabled_audiences
            if int(a.get('Destination Count', '0')) == 0
        ]

        # Industry-specific recommendations
        if 'Media/Publishing' in industries:
            recommendations.extend(self._media_use_cases(
                audiences, audiences_without_destinations
            ))

        if 'SaaS' in industries:
            recommendations.extend(self._saas_use_cases(
                audiences, audiences_without_destinations
            ))

        if 'eCommerce' in industries:
            recommendations.extend(self._ecommerce_use_cases(
                audiences, audiences_without_destinations
            ))

        # Universal recommendations based on patterns
        recommendations.extend(self._universal_use_cases(
            audiences, audiences_without_destinations
        ))

        return recommendations

    def _media_use_cases(self, all_audiences: List[Dict], unactivated: List[Dict]) -> List[Dict]:
        """Media/Publishing specific use cases"""
        use_cases = []

        # Newsletter subscriber segmentation
        subscriber_audiences = [
            a for a in all_audiences
            if 'subscriber' in a.get('Name', '').lower() or 'newsletter' in a.get('Name', '').lower()
        ]

        if subscriber_audiences:
            unactivated_subscribers = [a for a in subscriber_audiences if a in unactivated]
            if unactivated_subscribers:
                use_cases.append({
                    'category': 'Newsletter Engagement',
                    'opportunity': f"{len(unactivated_subscribers)} subscriber segments not activated",
                    'use_case': 'Connect subscriber segments to email platform (Braze/Iterable) for personalized newsletter delivery',
                    'specific_actions': [
                        'Segment by engagement level (active, at-risk, churned)',
                        'Create re-engagement campaigns for inactive readers',
                        'A/B test subject lines by subscriber segment',
                        'Send content recommendations based on reading behavior'
                    ],
                    'impact': 'Improve open rates 15-20%, reduce churn 10-15%'
                })

        # Engagement scoring
        engagement_audiences = [
            a for a in all_audiences
            if any(word in a.get('Name', '').lower() for word in ['engaged', 'active', 'open', 'rate'])
        ]

        if engagement_audiences:
            use_cases.append({
                'category': 'Content Personalization',
                'opportunity': f"{len(engagement_audiences)} engagement-based segments built",
                'use_case': 'Use engagement scores to personalize content recommendations and optimize send times',
                'specific_actions': [
                    'Connect to analytics platform (Amplitude/Mixpanel)',
                    'Build content affinity models',
                    'Optimize send times per segment',
                    'Create lookalike audiences from highly engaged readers'
                ],
                'impact': 'Increase content consumption 20-30%, grow engaged audience'
            })

        return use_cases

    def _saas_use_cases(self, all_audiences: List[Dict], unactivated: List[Dict]) -> List[Dict]:
        """SaaS specific use cases"""
        use_cases = []

        # Trial conversion
        trial_audiences = [
            a for a in all_audiences
            if 'trial' in a.get('Name', '').lower()
        ]

        if trial_audiences:
            use_cases.append({
                'category': 'Trial Conversion',
                'opportunity': f"{len(trial_audiences)} trial-related segments",
                'use_case': 'Build trial conversion funnel with targeted onboarding',
                'specific_actions': [
                    'Connect to product analytics (Amplitude/Mixpanel)',
                    'Track feature adoption during trial',
                    'Send contextual onboarding emails',
                    'Alert sales when trial users hit activation milestones'
                ],
                'impact': 'Improve trial-to-paid conversion 10-20%'
            })

        # Churn prevention
        churn_audiences = [
            a for a in all_audiences
            if any(word in a.get('Name', '').lower() for word in ['churn', 'inactive', 'at-risk'])
        ]

        if churn_audiences:
            use_cases.append({
                'category': 'Retention',
                'opportunity': f"{len(churn_audiences)} churn/retention segments",
                'use_case': 'Proactive churn prevention and win-back campaigns',
                'specific_actions': [
                    'Alert customer success team for high-value at-risk accounts',
                    'Send feature education to low-usage customers',
                    'Offer incentives to re-activate churned users',
                    'Build predictive churn models'
                ],
                'impact': 'Reduce churn 5-10%, increase customer LTV'
            })

        return use_cases

    def _ecommerce_use_cases(self, all_audiences: List[Dict], unactivated: List[Dict]) -> List[Dict]:
        """eCommerce specific use cases"""
        use_cases = []

        # Cart abandonment
        cart_audiences = [
            a for a in all_audiences
            if any(word in a.get('Name', '').lower() for word in ['cart', 'abandon', 'checkout'])
        ]

        if cart_audiences:
            use_cases.append({
                'category': 'Cart Recovery',
                'opportunity': f"{len(cart_audiences)} cart/checkout segments",
                'use_case': 'Automated cart abandonment recovery campaigns',
                'specific_actions': [
                    'Send email reminders 1hr, 24hr, 7 days after abandonment',
                    'Offer incentives for high-value carts',
                    'Retarget with dynamic product ads',
                    'SMS reminders for mobile cart abandoners'
                ],
                'impact': 'Recover 10-15% of abandoned carts'
            })

        return use_cases

    def _universal_use_cases(self, all_audiences: List[Dict], unactivated: List[Dict]) -> List[Dict]:
        """Universal use cases applicable to any business"""
        use_cases = []

        # Large unactivated audiences
        large_unactivated = [
            a for a in unactivated
            if int(a.get('Size', '0').replace(',', '') or '0') > 10000
        ]

        if large_unactivated:
            total_users = sum(int(a.get('Size', '0').replace(',', '') or '0') for a in large_unactivated)
            use_cases.append({
                'category': 'Activation Gap',
                'opportunity': f"{len(large_unactivated)} large audiences ({total_users:,} users) not activated",
                'use_case': 'Connect high-value segments to marketing platforms',
                'specific_actions': [
                    f"Priority audiences: {', '.join([a.get('Name', '')[:40] for a in large_unactivated[:3]])}",
                    'Connect to email/messaging platform (Braze, Iterable, Customer.io)',
                    'Sync to ad platforms for lookalike targeting (Google Ads, Facebook)',
                    'Enable personalization on website/app'
                ],
                'impact': f'Unlock {total_users:,} users for targeted campaigns'
            })

        # Folder-based organization insights
        folders = Counter([a.get('Folder', '') for a in all_audiences if a.get('Folder', '')])
        if folders:
            top_folders = folders.most_common(3)
            use_cases.append({
                'category': 'Audience Organization',
                'opportunity': f"Audiences organized in {len(folders)} folders",
                'use_case': 'Leverage existing segmentation strategy',
                'specific_actions': [
                    f"Top folders: {', '.join([f[0] for f in top_folders])}",
                    'Ensure folder-based strategy aligns with activation plan',
                    'Consider folder-level destination connections',
                    'Document use case per folder for team alignment'
                ],
                'impact': 'Improve team productivity and activation strategy'
            })

        return use_cases


# CLI usage
if __name__ == '__main__':
    analyzer = BusinessContextAnalyzer()
    context = analyzer.analyze_business_context()

    print("=== Business Context Analysis ===\n")
    print(f"Likely Industries: {', '.join(context['likely_industries'])}\n")

    print("=== Audience Patterns ===")
    patterns = context['audience_patterns']
    print(f"Total: {patterns.get('total_audiences', 0)}")
    print(f"Enabled: {patterns.get('enabled_count', 0)}")
    print(f"With Users: {patterns.get('with_users', 0)}\n")

    print("=== Use Case Opportunities ===")
    for i, rec in enumerate(context['use_case_opportunities'], 1):
        print(f"\n{i}. {rec['category']}: {rec['opportunity']}")
        print(f"   Use Case: {rec['use_case']}")
        print(f"   Impact: {rec['impact']}")
