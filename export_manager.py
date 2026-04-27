#!/usr/bin/env python3
"""
Export Manager - Generate CSV exports for audit data and recommendations
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import io
from business_context_analyzer import BusinessContextAnalyzer


class ExportManager:
    """Handles all CSV export operations"""

    def __init__(self, audit_data_dir: str = './audit_data'):
        self.data_dir = Path(audit_data_dir)
        self.analyzer = BusinessContextAnalyzer(audit_data_dir)

    def export_recommendations_csv(self, recommendations: Dict[str, Any]) -> str:
        """
        Export recommendations to CSV format with context-aware use cases
        Returns CSV as string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Analyze business context once
        business_context = self.analyzer.analyze_business_context()

        # Header
        writer.writerow([
            'Priority',
            'Severity',
            'Type',
            'Title',
            'Evidence',
            'Impact',
            'Recommendation',
            'Affected Count',
            'Use Case Examples',
            'Detected Business Model'
        ])

        # Findings
        for idx, finding in enumerate(recommendations.get('findings', []), 1):
            # Generate contextual use cases based on actual data
            use_cases = self._generate_contextual_use_cases(finding, business_context)

            writer.writerow([
                idx,
                finding.get('severity', 'unknown'),
                finding.get('type', 'unknown'),
                finding.get('title', ''),
                finding.get('evidence', ''),
                finding.get('impact', ''),
                finding.get('recommendation', ''),
                finding.get('count', 0),
                use_cases,
                ', '.join(business_context.get('likely_industries', ['General']))
            ])

        return output.getvalue()

    def _generate_contextual_use_cases(self, finding: Dict[str, Any], business_context: Dict[str, Any]) -> str:
        """Generate contextual use cases based on actual business model and data"""
        finding_type = finding.get('type', '')
        industries = business_context.get('likely_industries', ['General'])

        # Get relevant use case opportunities from business context
        relevant_opportunities = [
            opp for opp in business_context.get('use_case_opportunities', [])
            if self._is_relevant_to_finding(opp, finding_type)
        ]

        # Build contextual use cases
        use_cases = []

        if finding_type == 'activation_gap':
            # Use actual detected patterns
            if 'Media/Publishing' in industries:
                use_cases.append("Newsletter Campaigns: Activate subscriber segments in Braze/Iterable for personalized sends")
                use_cases.append("Content Recommendations: Use engagement scores to recommend relevant articles/topics")
                use_cases.append("Reader Re-engagement: Build win-back campaigns for inactive subscribers")

            if 'SaaS' in industries:
                use_cases.append("Product Onboarding: Send contextual emails based on feature usage patterns")
                use_cases.append("Trial Conversion: Alert sales when trial users hit activation milestones")
                use_cases.append("Expansion Revenue: Target power users with upsell/cross-sell offers")

            if 'eCommerce' in industries:
                use_cases.append("Cart Recovery: Automated abandonment emails with product recommendations")
                use_cases.append("Loyalty Programs: Reward high-value customers with exclusive offers")
                use_cases.append("Retargeting: Sync to Google/Facebook Ads for lookalike audiences")

            # Universal recommendations
            use_cases.append("Paid Media: Create lookalike audiences in ad platforms")
            use_cases.append("Analytics: Track segment performance across activation channels")

        elif finding_type == 'underutilized_source':
            if 'Media/Publishing' in industries:
                use_cases.append("Engagement Scoring: Build audiences from article views, reading time")
                use_cases.append("Content Affinity: Segment by topic preferences for personalization")
            else:
                use_cases.append("Behavioral Targeting: Build audiences from high-volume user actions")
                use_cases.append("Conversion Funnels: Track user journeys from events to outcomes")

            use_cases.append("Retention Analysis: Identify drop-off points in user lifecycle")
            use_cases.append("Feature Adoption: Track and segment by product usage patterns")
            use_cases.append("Attribution Models: Connect engagement events to conversions")

        elif finding_type == 'unused_high_volume':
            use_cases.append("Event-Triggered Campaigns: Send messages based on specific user actions")
            use_cases.append("Predictive Models: Build scoring from behavioral event patterns")
            use_cases.append("Journey Orchestration: Create multi-step flows based on event sequences")
            use_cases.append("Real-time Personalization: React to high-volume events with dynamic content")
            use_cases.append("Cohort Analysis: Build and compare user segments by event behavior")

        elif finding_type == 'personalization_opportunity':
            use_cases.append("Dynamic Content: Show different website/email content by user attributes")
            use_cases.append("A/B Testing: Create test variants by segment characteristics")
            use_cases.append("Recommendation Engine: Personalize suggestions using trait data")
            use_cases.append("Send Time Optimization: Schedule messages based on user timezone/behavior")
            use_cases.append("Landing Page Variants: Customize CTAs and messaging by segment")

        elif finding_type in ['stale_audience', 'workspace_hygiene']:
            use_cases.append("Workspace Cleanup: Remove outdated segments to improve team productivity")
            use_cases.append("Performance Optimization: Free up computation resources")
            use_cases.append("Logic Audit: Review and fix broken audience definitions")
            use_cases.append("Documentation: Update audience descriptions and use cases")
            use_cases.append("Cost Management: Stop syncing empty segments to reduce destination costs")

        elif finding_type == 'delivery_issue':
            use_cases.append("Data Quality: Fix schema mismatches causing sync failures")
            use_cases.append("Credential Audit: Verify destination API keys and permissions")
            use_cases.append("Monitoring: Set up alerts for delivery failures and drops")
            use_cases.append("Vendor Support: Escalate persistent issues to destination teams")
            use_cases.append("Fallback Strategy: Implement backup destinations for critical audiences")

        else:
            # Generic fallback
            use_cases.append("Improve data quality and activation effectiveness")

        # Format as numbered list
        if len(use_cases) > 5:
            use_cases = use_cases[:5]

        formatted = "Use Cases:\n" + "\n".join([f"{i+1}. {uc}" for i, uc in enumerate(use_cases)])
        return formatted

    def _is_relevant_to_finding(self, opportunity: Dict[str, Any], finding_type: str) -> bool:
        """Check if a use case opportunity is relevant to a finding type"""
        relevance_map = {
            'activation_gap': ['Newsletter Engagement', 'Trial Conversion', 'Cart Recovery', 'Activation Gap'],
            'underutilized_source': ['Content Personalization', 'Product Analytics'],
            'unused_high_volume': ['Product Analytics', 'Content Personalization'],
        }

        relevant_categories = relevance_map.get(finding_type, [])
        return opportunity.get('category', '') in relevant_categories

    def export_sources_with_destinations_csv(self) -> str:
        """
        Export sources with their destinations and event volumes
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Source Name',
            'Source ID',
            'Source Type',
            'Enabled',
            'Destinations Connected',
            'Destination Names',
            'Warehouses Connected',
            'Warehouse Names',
            '7-Day Event Volume',
            'Top Events'
        ])

        # Load sources data from Gateway API ONLY
        sources_file = self.data_dir / 'gateway_sources.csv'

        if not sources_file.exists():
            return "No Gateway API sources data found (gateway_sources.csv missing)"

        # Event volumes not available in Gateway API yet
        event_volumes = {}

        # Read sources
        with open(sources_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Gateway API column names
                source_name = row.get('Name', '')
                source_id = row.get('ID', '')
                source_type = row.get('Type', '')
                status = row.get('Status', '')
                enabled = 'true' if status == 'ENABLED' else 'false'

                # Get destinations (Gateway API format)
                dest_names = row.get('Connected Destinations', '')
                dest_count = len(dest_names.split(',')) if dest_names and dest_names.strip() else 0

                # Get warehouses (Gateway API format)
                wh_names = row.get('Connected Warehouses', '')
                wh_count = len(wh_names.split(',')) if wh_names and wh_names.strip() else 0

                # Event volumes not available in Gateway API yet
                volume = ''

                writer.writerow([
                    source_name,
                    source_id,
                    source_type,
                    enabled,
                    dest_count,
                    dest_names,
                    wh_count,
                    wh_names,
                    volume,
                    ''  # Top events - would need event schema data
                ])

        return output.getvalue()

    def export_audiences_with_destinations_csv(self) -> str:
        """
        Export audiences with their destinations
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Audience Name',
            'Audience ID',
            'Space',
            'Enabled',
            'Size',
            'Destinations Connected',
            'Destination Names',
            'Destination Types',
            'Created Date',
            'Last Modified',
            'Sources Used',
            'Events Used',
            'Traits Used',
            'Use Case Recommendation'
        ])

        # Load audiences data from Gateway API ONLY
        audiences_file = self.data_dir / 'gateway_audiences.csv'

        if not audiences_file.exists():
            return "No Gateway API audiences data found (gateway_audiences.csv missing)"

        # Read audiences
        with open(audiences_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                audience_name = row.get('Name') or row.get('name', '')
                audience_id = row.get('ID') or row.get('id', '')
                space = row.get('Space') or row.get('space_name', '')
                enabled = row.get('Enabled') or row.get('enabled', '')
                size = row.get('Size') or row.get('size', '0')

                # Destinations (Gateway API format)
                dest_count = row.get('Destination Count', '0')
                dest_names = row.get('Destinations', '')
                dest_types = ''  # Not available in Gateway API format yet

                # Metadata (Gateway API doesn't have modified date yet)
                created = ''  # Not in Gateway API CSV
                modified = ''  # Not in Gateway API CSV

                # Definition info (would need to parse Definition JSON)
                sources = ''  # Would need to extract from Definition
                events = ''   # Would need to extract from Definition
                traits = ''   # Would need to extract from Definition

                # Generate use case recommendation
                use_case = self._recommend_audience_use_case(row)

                writer.writerow([
                    audience_name,
                    audience_id,
                    space,
                    enabled,
                    size,
                    dest_count,
                    dest_names,
                    dest_types,
                    created,
                    modified,
                    sources,
                    events,
                    traits,
                    use_case
                ])

        return output.getvalue()

    def _recommend_audience_use_case(self, audience: Dict[str, str]) -> str:
        """Recommend use cases based on audience characteristics and business context"""
        name = audience.get('Name', '').lower()
        size = audience.get('Size', '0')
        dest_count = int(audience.get('Destination Count', '0'))

        try:
            size_int = int(size.replace(',', '')) if size and size != 'Computing...' else 0
        except (ValueError, AttributeError):
            size_int = 0

        # Get business context for smarter recommendations
        business_context = self.analyzer.analyze_business_context()
        industries = business_context.get('likely_industries', ['General'])

        # Build contextual recommendation
        recommendations = []

        # Size-based context
        size_context = ""
        if size_int == 0:
            return "Review logic or delete (empty audience)"
        elif size_int > 1000000:
            size_context = "Large reach - "
        elif size_int < 100:
            size_context = "Small test segment - "

        # Pattern matching with industry context
        if 'newsletter' in name or 'subscriber' in name:
            if 'Media/Publishing' in industries:
                recommendations.append("Send personalized newsletter campaigns")
                recommendations.append("segment by engagement level for content targeting")
                recommendations.append("build re-engagement flows for inactive readers")
            else:
                recommendations.append("Email marketing campaigns")
                recommendations.append("newsletter personalization")

        elif 'trial' in name or 'signup' in name:
            if 'SaaS' in industries:
                recommendations.append("Product onboarding sequence")
                recommendations.append("track feature adoption milestones")
                recommendations.append("alert sales on high-intent actions")
            else:
                recommendations.append("Trial conversion campaigns")
                recommendations.append("onboarding emails")

        elif 'cart' in name or 'abandon' in name or 'checkout' in name:
            recommendations.append("Cart abandonment recovery emails")
            recommendations.append("retargeting ads with dynamic products")
            recommendations.append("SMS reminders for high-value carts")

        elif 'churn' in name or 'at-risk' in name or 'inactive' in name:
            recommendations.append("Win-back campaigns with incentives")
            recommendations.append("retention offers")
            recommendations.append("CSM outreach for high-value accounts")

        elif 'engagement' in name or 'active' in name or 'engaged' in name:
            if 'Media/Publishing' in industries:
                recommendations.append("Content recommendations based on reading behavior")
                recommendations.append("early access to premium content")
            else:
                recommendations.append("Upsell campaigns")
                recommendations.append("referral program invitations")

        elif 'pro' in name or 'premium' in name or 'subscription' in name:
            recommendations.append("Premium feature education")
            recommendations.append("exclusive content/offers")
            recommendations.append("account management touchpoints")

        elif 'local' in name or 'geo' in name or 'national' in name:
            recommendations.append("Location-based content personalization")
            recommendations.append("geo-targeted campaigns")
            recommendations.append("regional event invitations")

        elif 'deal' in name or 'vertical' in name:
            recommendations.append("Industry-specific content/offers")
            recommendations.append("vertical-focused campaigns")
            recommendations.append("targeted account outreach")

        # Activation status
        if dest_count == 0 and size_int > 1000:
            recommendations.append("[ACTIVATION OPPORTUNITY: Connect to marketing tools]")

        # Build final recommendation
        if recommendations:
            return size_context + ", ".join(recommendations[:3])
        elif size_int > 1000000:
            return "Broad awareness campaigns, brand messaging, lookalike modeling"
        else:
            return "Targeted campaigns, personalized messaging, behavioral triggers"

    def export_top_events_csv(self) -> str:
        """
        Export top events by volume
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Event Name',
            '7-Day Volume',
            'Used in Audiences',
            'Audience Count',
            'Priority',
            'Recommended Actions'
        ])

        # Load event coverage
        events_file = self.data_dir / 'event_coverage.csv'
        if events_file.exists():
            with open(events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    event_name = row.get('Event', '')
                    usage_count = row.get('Usage Count', '0')

                    try:
                        count = int(usage_count)
                    except ValueError:
                        count = 0

                    # Determine priority
                    if count > 50:
                        priority = 'HIGH - Core event'
                        action = 'Ensure tracked consistently across all sources'
                    elif count > 10:
                        priority = 'MEDIUM - Important'
                        action = 'Monitor for schema changes'
                    elif count > 0:
                        priority = 'LOW - Used'
                        action = 'Document use cases'
                    else:
                        priority = 'UNUSED'
                        action = 'Consider building audiences from this event'

                    writer.writerow([
                        event_name,
                        '',  # Volume data would need event volumes by event
                        'Yes' if count > 0 else 'No',
                        count,
                        priority,
                        action
                    ])

        return output.getvalue()

    def export_all_as_zip(self, recommendations: Dict[str, Any] = None) -> bytes:
        """
        Export all data as a ZIP file
        Returns ZIP file as bytes
        """
        import zipfile
        from io import BytesIO

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Recommendations
            if recommendations:
                zip_file.writestr(
                    'recommendations.csv',
                    self.export_recommendations_csv(recommendations)
                )

            # Sources with destinations
            zip_file.writestr(
                'sources_with_destinations.csv',
                self.export_sources_with_destinations_csv()
            )

            # Audiences with destinations
            zip_file.writestr(
                'audiences_with_destinations.csv',
                self.export_audiences_with_destinations_csv()
            )

            # Top events
            zip_file.writestr(
                'top_events.csv',
                self.export_top_events_csv()
            )

            # Add summary
            summary = self._generate_summary(recommendations)
            zip_file.writestr('README.txt', summary)

        zip_buffer.seek(0)
        return zip_buffer.read()

    def _generate_summary(self, recommendations: Dict[str, Any] = None) -> str:
        """Generate README summary for exports"""
        # Use Gateway API summary
        summary_file = self.data_dir / 'gateway_summary.json'
        summary_data = {}

        if summary_file.exists():
            with open(summary_file) as f:
                summary_data = json.load(f)
        else:
            print("⚠️  WARNING: gateway_summary.json not found")

        text = f"""Segment Workspace Audit Export (Gateway API)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Workspace: {summary_data.get('workspace_slug', 'Unknown')}
Customer: {summary_data.get('customer_name', 'Unknown')}
Audit Date: {summary_data.get('audit_date', 'Unknown')}

=== Summary ===
Total Sources: {summary_data.get('sources_count', 0)}
Total Audiences: {summary_data.get('audiences_count', 0)}
Total Spaces: {summary_data.get('spaces_count', 0)}
Total Findings: {recommendations.get('total_findings', 0) if recommendations else 0}

=== Files Included ===
1. recommendations.csv - Prioritized findings and recommendations with use cases
2. sources_with_destinations.csv - All sources and their connected destinations
3. audiences_with_destinations.csv - All audiences and their activation status
4. top_events.csv - Event usage analysis and recommendations

=== How to Use ===
- Review recommendations.csv first for priority actions
- Use sources_with_destinations.csv to audit data collection
- Use audiences_with_destinations.csv to identify activation gaps
- Use top_events.csv to understand event patterns

=== Next Steps ===
1. Review high-priority recommendations
2. Identify quick wins (low effort, high impact)
3. Connect unactivated audiences to destinations
4. Clean up empty or disabled audiences
5. Build event-based audiences from high-volume events

For questions, contact your Segment Customer Success Manager.
"""
        return text


# CLI usage
if __name__ == '__main__':
    import sys

    exporter = ExportManager()

    if len(sys.argv) > 1:
        export_type = sys.argv[1]

        if export_type == 'recommendations':
            # Load recommendations
            from recommendations_engine import generate_recommendations
            recs = generate_recommendations()
            print(exporter.export_recommendations_csv(recs))

        elif export_type == 'sources':
            print(exporter.export_sources_with_destinations_csv())

        elif export_type == 'audiences':
            print(exporter.export_audiences_with_destinations_csv())

        elif export_type == 'events':
            print(exporter.export_top_events_csv())

        elif export_type == 'all':
            from recommendations_engine import generate_recommendations
            recs = generate_recommendations()
            zip_data = exporter.export_all_as_zip(recs)

            # Write to file
            output_file = 'segment_audit_export.zip'
            with open(output_file, 'wb') as f:
                f.write(zip_data)
            print(f"Exported to {output_file}")
    else:
        print("Usage: python export_manager.py [recommendations|sources|audiences|events|all]")
