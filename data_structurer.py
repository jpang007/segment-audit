#!/usr/bin/env python3
"""
Data Structurer - Converts raw audit data into curated context blocks for Gemini
Implements best practice: "feed it signal, not raw data"
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter


class DataStructurer:
    """Structures audit data into high-signal context blocks for LLM consumption"""

    def __init__(self, audit_data_dir: str = './audit_data'):
        self.data_dir = Path(audit_data_dir)

    def structure_for_gemini(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw findings into curated context blocks
        This is the key transformation: signal, not noise

        Returns structured data ready for multi-layer prompting
        """

        # Load raw data
        audiences = self._load_audiences()
        sources = self._load_sources()
        summary = self._load_summary()

        structured = {
            "workspace_summary": self._build_workspace_summary(summary, sources, audiences),
            "source_insights": self._build_source_insights(sources),
            "audience_insights": self._build_audience_insights(audiences, findings),
            "event_insights": self._build_event_insights(audiences),
            "destination_summary": self._build_destination_summary(sources, audiences),
            "findings_summary": self._build_findings_summary(findings),
            "opportunities": self._identify_opportunities(audiences, sources, findings)
        }

        return structured

    def _load_summary(self) -> Dict:
        """Load gateway summary"""
        summary_file = self.data_dir / 'gateway_summary.json'
        if summary_file.exists():
            with open(summary_file) as f:
                return json.load(f)
        return {}

    def _load_sources(self) -> List[Dict]:
        """Load sources from Gateway API"""
        sources_file = self.data_dir / 'gateway_sources.csv'
        if not sources_file.exists():
            return []

        sources = []
        with open(sources_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sources.append(row)
        return sources

    def _load_audiences(self) -> List[Dict]:
        """Load audiences from Gateway API"""
        audiences_file = self.data_dir / 'gateway_audiences.csv'
        if not audiences_file.exists():
            return []

        audiences = []
        with open(audiences_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                audiences.append(row)
        return audiences

    def _build_workspace_summary(self, summary: Dict, sources: List[Dict], audiences: List[Dict]) -> Dict:
        """High-level workspace metrics"""
        enabled_sources = len([s for s in sources if s.get('Status') == 'ENABLED'])
        enabled_audiences = len([a for a in audiences if a.get('Enabled', '').lower() == 'true'])

        # Calculate total users across enabled audiences
        total_users = 0
        for aud in audiences:
            if aud.get('Enabled', '').lower() == 'true':
                size_str = aud.get('Size', '0')
                try:
                    size = int(size_str.replace(',', '')) if size_str and size_str not in ['Computing...', ''] else 0
                    total_users += size
                except (ValueError, AttributeError):
                    pass

        return {
            "workspace_slug": summary.get('workspace_slug', 'unknown'),
            "customer_name": summary.get('customer_name', 'unknown'),
            "total_sources": len(sources),
            "enabled_sources": enabled_sources,
            "total_audiences": len(audiences),
            "enabled_audiences": enabled_audiences,
            "total_users_in_audiences": total_users,
            "spaces": summary.get('spaces_count', 0)
        }

    def _build_source_insights(self, sources: List[Dict]) -> List[Dict]:
        """Extract actionable source insights"""
        insights = []

        for src in sources:
            status = src.get('Status', '')
            name = src.get('Name', '')
            source_type = src.get('Type', '')
            destinations = src.get('Connected Destinations', '')
            dest_list = [d.strip() for d in destinations.split(',') if d.strip()]

            insight = {
                "name": name,
                "type": source_type,
                "status": status,
                "destination_count": len(dest_list),
                "destinations": dest_list if dest_list else []
            }

            # Add signal: underutilized if enabled but no destinations
            if status == 'ENABLED' and len(dest_list) == 0:
                insight["signal"] = "underutilized"
            elif status == 'DISABLED':
                insight["signal"] = "disabled"
            elif status == 'NO_RECENT_DATA':
                insight["signal"] = "stale"
            else:
                insight["signal"] = "healthy"

            insights.append(insight)

        # Sort by signal (issues first)
        insights.sort(key=lambda x: {'underutilized': 0, 'stale': 1, 'disabled': 2, 'healthy': 3}[x['signal']])

        return insights[:20]  # Top 20 most relevant

    def _build_audience_insights(self, audiences: List[Dict], findings: Dict) -> List[Dict]:
        """Extract actionable audience insights"""
        insights = []

        for aud in audiences:
            enabled = aud.get('Enabled', '').lower() == 'true'
            name = aud.get('Name', '')
            size_str = aud.get('Size', '0')
            dest_count_str = aud.get('Destination Count', '0')
            space = aud.get('Space', '')
            folder = aud.get('Folder', '')

            try:
                size = int(size_str.replace(',', '')) if size_str and size_str not in ['Computing...', ''] else 0
            except (ValueError, AttributeError):
                size = 0

            try:
                dest_count = int(dest_count_str) if dest_count_str else 0
            except (ValueError, AttributeError):
                dest_count = 0

            # Only include audiences with signal
            if not enabled and size == 0:
                continue  # Skip disabled empty audiences

            insight = {
                "name": name,
                "size": size,
                "enabled": enabled,
                "destination_count": dest_count,
                "space": space,
                "folder": folder if folder else None,
                "category": self._categorize_audience(name)
            }

            # Add actionable signal
            if enabled and size > 0 and dest_count == 0:
                insight["signal"] = "activation_opportunity"
                insight["priority"] = "high" if size > 10000 else "medium"
            elif enabled and size == 0:
                insight["signal"] = "empty_enabled"
                insight["priority"] = "low"
            elif not enabled and size > 1000:
                insight["signal"] = "disabled_with_users"
                insight["priority"] = "medium"
            else:
                insight["signal"] = "active"
                insight["priority"] = "low"

            insights.append(insight)

        # Sort by priority (high impact first)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        insights.sort(key=lambda x: (priority_order[x['priority']], -x['size']))

        return insights[:50]  # Top 50 most actionable

    def _categorize_audience(self, name: str) -> str:
        """Categorize audience by name patterns"""
        name_lower = name.lower()

        if any(word in name_lower for word in ['newsletter', 'subscriber', 'subscription']):
            return 'subscription'
        elif any(word in name_lower for word in ['trial', 'signup', 'new']):
            return 'acquisition'
        elif any(word in name_lower for word in ['churn', 'inactive', 'at-risk']):
            return 'retention'
        elif any(word in name_lower for word in ['pro', 'premium', 'vip', 'high-value']):
            return 'monetization'
        elif any(word in name_lower for word in ['engagement', 'active', 'power']):
            return 'engagement'
        elif any(word in name_lower for word in ['local', 'geo', 'region']):
            return 'geographic'
        elif any(word in name_lower for word in ['test', 'example', 'demo']):
            return 'test'
        else:
            return 'general'

    def _build_event_insights(self, audiences: List[Dict]) -> List[Dict]:
        """Extract event patterns from audience definitions (when available)"""
        # Note: Gateway API has Definition field but it's JSON blob
        # For now, return placeholder - can be enhanced when we parse definitions
        return []

    def _build_destination_summary(self, sources: List[Dict], audiences: List[Dict]) -> Dict:
        """Summarize destination landscape"""
        all_destinations = set()

        # From sources
        for src in sources:
            dests = src.get('Connected Destinations', '')
            if dests:
                for d in dests.split(','):
                    if d.strip():
                        all_destinations.add(d.strip())

        # From audiences
        for aud in audiences:
            dests = aud.get('Destinations', '')
            if dests:
                for d in dests.split(','):
                    if d.strip():
                        all_destinations.add(d.strip())

        # Categorize destinations
        destination_types = {
            'email': [],
            'analytics': [],
            'ads': [],
            'warehouse': [],
            'other': []
        }

        for dest in all_destinations:
            dest_lower = dest.lower()
            if any(word in dest_lower for word in ['braze', 'iterable', 'customer.io', 'sendgrid', 'mailchimp']):
                destination_types['email'].append(dest)
            elif any(word in dest_lower for word in ['amplitude', 'mixpanel', 'heap', 'analytics']):
                destination_types['analytics'].append(dest)
            elif any(word in dest_lower for word in ['google ads', 'facebook', 'linkedin', 'tiktok', 'twitter']):
                destination_types['ads'].append(dest)
            elif any(word in dest_lower for word in ['snowflake', 'redshift', 'bigquery', 's3', 'warehouse']):
                destination_types['warehouse'].append(dest)
            else:
                destination_types['other'].append(dest)

        return {
            "total_unique_destinations": len(all_destinations),
            "all_destinations": sorted(list(all_destinations)),
            "by_category": {k: sorted(v) for k, v in destination_types.items() if v}
        }

    def _build_findings_summary(self, findings: Dict) -> Dict:
        """Summarize findings in digestible format"""
        return {
            "total_findings": findings.get('total_findings', 0),
            "high_priority": findings.get('high_priority', 0),
            "medium_priority": findings.get('medium_priority', 0),
            "low_priority": findings.get('low_priority', 0),
            "finding_types": [f.get('type') for f in findings.get('findings', [])]
        }

    def _identify_opportunities(self, audiences: List[Dict], sources: List[Dict], findings: Dict) -> List[Dict]:
        """Identify specific opportunities (not just problems)"""
        opportunities = []

        # Opportunity 1: Large unactivated audiences
        large_unactivated = []
        for aud in audiences:
            if aud.get('Enabled', '').lower() == 'true':
                size_str = aud.get('Size', '0')
                dest_count = int(aud.get('Destination Count', '0') or 0)

                try:
                    size = int(size_str.replace(',', '')) if size_str and size_str not in ['Computing...', ''] else 0
                except (ValueError, AttributeError):
                    size = 0

                if size > 10000 and dest_count == 0:
                    large_unactivated.append({
                        "name": aud.get('Name'),
                        "size": size,
                        "category": self._categorize_audience(aud.get('Name', ''))
                    })

        if large_unactivated:
            total_reach = sum(a['size'] for a in large_unactivated)
            opportunities.append({
                "type": "large_unactivated_audiences",
                "description": f"{len(large_unactivated)} audiences with {total_reach:,} total users not connected to any destination",
                "examples": sorted(large_unactivated, key=lambda x: x['size'], reverse=True)[:5],
                "potential_impact": "immediate activation opportunity"
            })

        # Opportunity 2: Underutilized sources
        underutilized_sources = [
            s.get('Name') for s in sources
            if s.get('Status') == 'ENABLED' and not s.get('Connected Destinations', '').strip()
        ]

        if underutilized_sources:
            opportunities.append({
                "type": "underutilized_sources",
                "description": f"{len(underutilized_sources)} enabled sources not sending data anywhere",
                "examples": underutilized_sources[:5],
                "potential_impact": "data collection without activation"
            })

        return opportunities


# CLI testing
if __name__ == '__main__':
    import sys

    structurer = DataStructurer()

    # Load findings
    from recommendations_engine import generate_recommendations
    findings = generate_recommendations()

    # Structure data
    structured = structurer.structure_for_gemini(findings)

    print("=== STRUCTURED DATA FOR GEMINI ===\n")
    print(json.dumps(structured, indent=2))
    print(f"\n=== SIZE: {len(json.dumps(structured))} characters ===")
