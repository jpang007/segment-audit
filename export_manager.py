#!/usr/bin/env python3
"""
Export Manager - Generate CSV exports for audit data
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import io


class ExportManager:
    """Handles all CSV export operations"""

    def __init__(self, audit_data_dir: str = './audit_data'):
        self.data_dir = Path(audit_data_dir)

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
        """Recommend use cases based on audience characteristics"""
        name = audience.get('Name', '').lower()
        size = audience.get('Size', '0')
        dest_count = int(audience.get('Destination Count', '0'))

        try:
            size_int = int(size.replace(',', '')) if size and size != 'Computing...' else 0
        except (ValueError, AttributeError):
            size_int = 0

        # Simple pattern-based recommendations
        industries = ['General']

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

    def export_all_as_zip(self) -> bytes:
        """
        Export all audit data as a comprehensive ZIP file
        Includes all raw data files, processed CSVs, and JSON exports
        Returns ZIP file as bytes
        """
        import zipfile
        from io import BytesIO

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # ===== PROCESSED EXPORTS (Analysis-ready CSVs) =====

            # Sources with destinations
            try:
                zip_file.writestr(
                    'processed/sources_with_destinations.csv',
                    self.export_sources_with_destinations_csv()
                )
            except Exception as e:
                print(f"Warning: Could not export sources_with_destinations: {e}")

            # Audiences with destinations
            try:
                zip_file.writestr(
                    'processed/audiences_with_destinations.csv',
                    self.export_audiences_with_destinations_csv()
                )
            except Exception as e:
                print(f"Warning: Could not export audiences_with_destinations: {e}")

            # Top events
            try:
                zip_file.writestr(
                    'processed/top_events.csv',
                    self.export_top_events_csv()
                )
            except Exception as e:
                print(f"Warning: Could not export top_events: {e}")

            # ===== RAW DATA FILES (All Gateway API data) =====

            # List of Gateway API files to include
            gateway_files = [
                'gateway_audiences.csv',
                'gateway_sources.csv',
                'gateway_profile_insights.csv',
                'gateway_space_sources.csv',
                'gateway_summary.json',
                'gateway_destinations.json',
                'gateway_audit_trail.json',
                'gateway_mtu.json',
                'gateway_usage_data.json',
                'gateway_data_flows.json',
                'gateway_personas_entitlements.json'
            ]

            # Add each Gateway file if it exists
            for filename in gateway_files:
                file_path = self.data_dir / filename
                if file_path.exists():
                    try:
                        with open(file_path, 'rb') as f:
                            zip_file.writestr(f'raw_data/{filename}', f.read())
                    except Exception as e:
                        print(f"Warning: Could not add {filename}: {e}")

            # ===== SOURCES JSON (for Gem analysis) =====

            # Include sources.json with full schema data
            sources_json = self.data_dir / 'gateway_sources.json'
            if sources_json.exists():
                try:
                    with open(sources_json, 'rb') as f:
                        zip_file.writestr('raw_data/gateway_sources.json', f.read())
                except Exception as e:
                    print(f"Warning: Could not add sources JSON: {e}")

            # ===== GEM ANALYSIS FILE (formatted for Gemini Gem) =====

            try:
                gem_data = self._generate_gem_analysis_file()
                zip_file.writestr('for_gem_analysis/workspace_audit_data.json', gem_data)
            except Exception as e:
                print(f"Warning: Could not generate Gem analysis file: {e}")

            # ===== DOCUMENTATION =====

            # Add comprehensive summary
            summary = self._generate_summary()
            zip_file.writestr('README.txt', summary)

            # Add file manifest
            manifest = self._generate_file_manifest()
            zip_file.writestr('FILE_MANIFEST.txt', manifest)

        zip_buffer.seek(0)
        return zip_buffer.read()

    def _generate_gem_analysis_file(self) -> str:
        """
        Generate a JSON file formatted for Gemini Gem analysis
        Includes all workspace data in a structure the Gem expects
        """
        # Load all necessary files
        summary_file = self.data_dir / 'gateway_summary.json'
        sources_file = self.data_dir / 'gateway_sources.json'
        destinations_file = self.data_dir / 'gateway_destinations.json'
        audiences_file = self.data_dir / 'gateway_audiences.csv'
        mtu_file = self.data_dir / 'gateway_mtu.json'
        audit_trail_file = self.data_dir / 'gateway_audit_trail.json'
        profile_insights_file = self.data_dir / 'gateway_profile_insights.csv'

        gem_data = {
            "workspace_summary": {},
            "sources": [],
            "destinations": [],
            "audiences": [],
            "mtu_data": {},
            "audit_trail_summary": {},
            "profile_insights": [],
            "business_context": "Add any relevant customer context here before uploading to Gem"
        }

        # Load summary
        if summary_file.exists():
            with open(summary_file) as f:
                gem_data["workspace_summary"] = json.load(f)

        # Load sources JSON (with full schema)
        if sources_file.exists():
            with open(sources_file) as f:
                gem_data["sources"] = json.load(f)

        # Load destinations
        if destinations_file.exists():
            with open(destinations_file) as f:
                gem_data["destinations"] = json.load(f)

        # Load audiences from CSV
        if audiences_file.exists():
            with open(audiences_file, 'r') as f:
                reader = csv.DictReader(f)
                gem_data["audiences"] = list(reader)

        # Load MTU data
        if mtu_file.exists():
            with open(mtu_file) as f:
                gem_data["mtu_data"] = json.load(f)

        # Load audit trail (summarized)
        if audit_trail_file.exists():
            with open(audit_trail_file) as f:
                audit_data = json.load(f)
                # Just include count and recent events
                gem_data["audit_trail_summary"] = {
                    "total_events": len(audit_data),
                    "recent_events": audit_data[:10] if len(audit_data) > 10 else audit_data
                }

        # Load profile insights from CSV
        if profile_insights_file.exists():
            with open(profile_insights_file, 'r') as f:
                reader = csv.DictReader(f)
                gem_data["profile_insights"] = list(reader)

        return json.dumps(gem_data, indent=2)

    def _generate_file_manifest(self) -> str:
        """Generate a manifest explaining all files in the ZIP"""
        return """Segment Workspace Audit - File Manifest
==========================================

This ZIP contains a complete export of your Segment workspace audit data.

📁 FOLDER STRUCTURE:
--------------------

/processed/
    Analysis-ready CSV files for immediate use:
    - sources_with_destinations.csv: Sources and their connected destinations
    - audiences_with_destinations.csv: Audiences and activation status
    - top_events.csv: Event usage analysis

/raw_data/
    Complete raw data from Segment Gateway API:
    - gateway_sources.csv: All sources (basic info)
    - gateway_sources.json: All sources with full schemas
    - gateway_audiences.csv: All audiences and their properties
    - gateway_destinations.json: All destinations and configs
    - gateway_mtu.json: MTU/API usage data with billing info
    - gateway_audit_trail.json: Workspace activity logs
    - gateway_usage_data.json: Usage metrics
    - gateway_data_flows.json: Onboarding use cases
    - gateway_profile_insights.csv: Identity resolution configs
    - gateway_space_sources.csv: Sources by Engage space
    - gateway_summary.json: High-level workspace summary
    - gateway_personas_entitlements.json: Engage/Unify features

/for_gem_analysis/
    Ready for AI analysis:
    - workspace_audit_data.json: Formatted for Gemini Gem analysis
      → Upload this file to your Segment SA Auditor Gem for recommendations

📖 QUICK START GUIDE:
--------------------

1. AI RECOMMENDATIONS:
   - Upload: for_gem_analysis/workspace_audit_data.json
   - To your Gemini Gem (Segment SA Auditor or Use Case Builder)
   - Get detailed SA-quality recommendations

2. SOURCE ANALYSIS:
   - Open: processed/sources_with_destinations.csv
   - Check for disabled production sources
   - Verify all sources have destinations

3. SOURCE ANALYSIS:
   - Open: processed/audiences_with_destinations.csv
   - Find audiences with 0 destinations
   - Identify high-user-count audiences to activate

4. DEEP DIVE:
   - Use raw_data/ files for detailed investigation
   - gateway_sources.json has full event schemas
   - gateway_audit_trail.json shows recent activity
   - gateway_mtu.json has billing/usage details

🎯 RECOMMENDED ORDER:
--------------------

1st → for_gem_analysis/ (AI analysis via Gemini Gem)
2nd → processed/sources_with_destinations.csv (data health)
3rd → processed/audiences_with_destinations.csv (activation gaps)
4th → raw_data/ (detailed investigation)

📊 DATA FRESHNESS:
-----------------

All data reflects the state of the workspace at audit time.
Check gateway_summary.json for exact audit date/time.

💡 NOTES:
---------

- CSV files open in Excel/Google Sheets
- JSON files open in any text editor (or use jsonviewer.stack.hu)
- For Gem analysis: Copy workspace_audit_data.json content
- For questions: Contact your Segment Customer Success Manager

==========================================
Generated by Segment Audit Dashboard
"""

    def _generate_summary(self) -> str:
        """Generate README summary for exports"""
        # Use Gateway API summary
        summary_file = self.data_dir / 'gateway_summary.json'
        summary_data = {}

        if summary_file.exists():
            with open(summary_file) as f:
                summary_data = json.load(f)
        else:
            print("⚠️  WARNING: gateway_summary.json not found")

        text = f"""SEGMENT WORKSPACE AUDIT - COMPLETE EXPORT
==========================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

WORKSPACE INFORMATION:
---------------------
Customer: {summary_data.get('customer_name', 'Unknown')}
Workspace: {summary_data.get('workspace_slug', 'Unknown')}
Audit Date: {summary_data.get('audit_date', 'Unknown')}

WORKSPACE METRICS:
-----------------
Total Sources: {summary_data.get('sources_count', 0)}
Total Destinations: {summary_data.get('destinations_count', 0)}
Total Audiences: {summary_data.get('audiences_count', 0)}
Total Journeys: {summary_data.get('journeys_count', 0)}
Total Campaigns: {summary_data.get('campaigns_count', 0)}
Total Spaces: {summary_data.get('spaces_count', 0)}

WHAT'S INCLUDED:
---------------

📂 /processed/ - Analysis-Ready Files
   ✓ sources_with_destinations.csv - Source connectivity audit
   ✓ audiences_with_destinations.csv - Activation gap analysis
   ✓ top_events.csv - Event usage patterns

📂 /raw_data/ - Complete Workspace Data
   ✓ All Gateway API JSON/CSV exports
   ✓ Full source schemas with event definitions
   ✓ MTU/API usage and billing data
   ✓ Audit trail activity logs
   ✓ Identity resolution configurations

📂 /for_gem_analysis/ - AI-Ready Format
   ✓ workspace_audit_data.json
   → Upload to Gemini Gem for detailed SA recommendations

QUICK START:
-----------

1. GET AI RECOMMENDATIONS:
   → Upload: for_gem_analysis/workspace_audit_data.json
   → To your Gemini Gem (Segment SA Auditor)
   → Receive detailed, confidence-rated findings

2. AUDIT DATA COLLECTION:
   → Open: processed/sources_with_destinations.csv
   → Check for disabled sources
   → Verify production sources are active

3. FIND ACTIVATION GAPS:
   → Open: processed/audiences_with_destinations.csv
   → Find audiences with 0 destinations
   → Prioritize high-user-count audiences

4. DEEP DIVE (if needed):
   → Explore raw_data/ for detailed investigation
   → gateway_sources.json has full event schemas
   → gateway_mtu.json has billing/usage metrics

PRIORITY ACTIONS:
----------------

P0 - Critical (Do Now):
• Re-enable any disabled production sources
• Fix broken destination connections
• Address compliance/data loss issues

P1 - High (This Week):
• Activate large audiences with 0 destinations
• Connect high-value segments to marketing tools
• Clean up stale rETL sources

P2 - Medium (This Month):
• Improve naming conventions
• Remove test/staging sources
• Organize audiences into folders

NEXT STEPS:
----------

1. Share this export with your team
2. Upload workspace_audit_data.json to Gemini Gem
3. Review AI recommendations for detailed guidance
4. Schedule implementation with customer
5. Follow up after 30 days to measure impact

SUPPORT:
-------

For questions about this audit or implementing recommendations:
→ Contact your Segment Customer Success Manager
→ Schedule an office hours session
→ Visit docs.segment.com for best practices

See FILE_MANIFEST.txt for detailed file descriptions.

==========================================
Powered by Segment Audit Dashboard
"""
        return text


# CLI usage
if __name__ == '__main__':
    import sys

    exporter = ExportManager()

    if len(sys.argv) > 1:
        export_type = sys.argv[1]

        if export_type == 'sources':
            print(exporter.export_sources_with_destinations_csv())

        elif export_type == 'audiences':
            print(exporter.export_audiences_with_destinations_csv())

        elif export_type == 'events':
            print(exporter.export_top_events_csv())

        elif export_type == 'all':
            zip_data = exporter.export_all_as_zip()

            # Write to file
            output_file = 'segment_audit_export.zip'
            with open(output_file, 'wb') as f:
                f.write(zip_data)
            print(f"Exported to {output_file}")
    else:
        print("Usage: python export_manager.py [sources|audiences|events|all]")
