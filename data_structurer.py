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
        destinations = self._load_destinations()
        profile_insights = self._load_profile_insights()
        space_sources = self._load_space_sources()
        journeys = self._load_journeys()

        structured = {
            "workspace_summary": self._build_workspace_summary(summary, sources, audiences),
            "source_insights": self._build_source_insights(sources),
            "schema_health": self._build_schema_health(sources),
            "audience_insights": self._build_audience_insights(audiences, findings),
            "event_insights": self._build_event_insights(audiences),
            "destination_summary": self._build_destination_summary(sources, audiences, destinations),
            "profile_insights": self._build_profile_insights_summary(profile_insights, space_sources),
            "journey_insights": self._build_journey_insights(journeys, audiences),
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

    def _load_destinations(self) -> Dict:
        """Load destinations from Gateway API"""
        destinations_file = self.data_dir / 'gateway_destinations.json'
        if destinations_file.exists():
            with open(destinations_file) as f:
                return json.load(f)
        return {'destinations': []}

    def _load_profile_insights(self) -> List[Dict]:
        """Load identity resolution configs (profile insights)"""
        insights_file = self.data_dir / 'gateway_profile_insights.csv'
        if not insights_file.exists():
            return []

        insights = []
        with open(insights_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                insights.append(row)
        return insights

    def _load_space_sources(self) -> List[Dict]:
        """Load space-to-source connections (critical for understanding data flow)"""
        space_sources_file = self.data_dir / 'gateway_space_sources.csv'
        if not space_sources_file.exists():
            return []

        space_sources = []
        with open(space_sources_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                space_sources.append(row)
        return space_sources

    def _load_journeys(self) -> List[Dict]:
        """Load journeys and campaigns from Gateway API"""
        journeys_file = self.data_dir / 'gateway_journeys.csv'
        if not journeys_file.exists():
            return []

        journeys = []
        with open(journeys_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                journeys.append(row)
        return journeys

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

    def _build_schema_health(self, sources: List[Dict]) -> Dict:
        """
        Analyze source schema health - detect event explosion and tracking plan issues
        CRITICAL: Event explosion (>1000 events) indicates dynamic event names, poor hygiene
        """
        schema_issues = []
        event_counts = []

        for src in sources:
            event_count_str = src.get('Event Count', '0')
            try:
                event_count = int(event_count_str) if event_count_str else 0
            except (ValueError, AttributeError):
                event_count = 0

            if event_count > 0:
                event_counts.append({
                    'name': src.get('Name', ''),
                    'event_count': event_count,
                    'status': src.get('Status', '')
                })

                # Flag event explosion (>1000 events is abnormal)
                if event_count > 1000:
                    schema_issues.append({
                        'source_name': src.get('Name', ''),
                        'source_slug': src.get('Slug', ''),
                        'source_id': src.get('ID', ''),
                        'event_count': event_count,
                        'status': src.get('Status', ''),
                        'severity': 'critical' if event_count > 3000 else 'high',
                        'issue_type': 'event_explosion',
                        'likely_cause': 'Dynamic event names (e.g., including IDs, timestamps, or UUIDs in event names)',
                        'impact': 'High MTU costs, slow UI performance, difficult to analyze data, tracking plan bloat'
                    })

        # Sort by event count
        event_counts.sort(key=lambda x: x['event_count'], reverse=True)

        return {
            'has_schema_issues': len(schema_issues) > 0,
            'total_issues': len(schema_issues),
            'issues': schema_issues,
            'top_sources_by_event_count': event_counts[:10],
            'max_event_count': max([e['event_count'] for e in event_counts]) if event_counts else 0,
            'sources_with_explosion': len([i for i in schema_issues if i['event_count'] > 1000])
        }

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

    def _build_journey_insights(self, journeys: List[Dict], audiences: List[Dict]) -> Dict:
        """
        Analyze Journeys/Campaigns - critical for understanding activation strategy
        Shows which destinations are being used for orchestration vs batch sync
        """
        if not journeys:
            return {
                "has_journeys": False,
                "message": "No Journeys or Campaigns found (Engage may not be enabled)"
            }

        # Separate journeys from campaigns
        journey_items = [j for j in journeys if j.get('Type') == 'Journey']
        campaign_items = [j for j in journeys if j.get('Type') == 'Campaign']

        # Analyze journey states
        active_journeys = [j for j in journey_items if j.get('Status', '').lower() in ['running', 'active']]
        draft_journeys = [j for j in journey_items if j.get('State', '').lower() == 'draft']
        published_journeys = [j for j in journey_items if j.get('State', '').lower() == 'published']

        # Analyze campaigns
        active_campaigns = [c for c in campaign_items if c.get('Status', '').lower() in ['running', 'active']]
        draft_campaigns = [c for c in campaign_items if c.get('State', '').lower() == 'draft']

        # Extract destination usage patterns
        journey_destinations = {}
        for journey in journey_items:
            dests = journey.get('Destinations', '')
            if dests:
                for dest in dests.split(','):
                    dest = dest.strip()
                    if dest:
                        journey_destinations[dest] = journey_destinations.get(dest, 0) + 1

        campaign_destinations = {}
        for campaign in campaign_items:
            dests = campaign.get('Destinations', '')
            if dests:
                for dest in dests.split(','):
                    dest = dest.strip()
                    if dest:
                        campaign_destinations[dest] = campaign_destinations.get(dest, 0) + 1

        # Identify top destinations used in orchestration
        all_journey_dests = {**journey_destinations, **campaign_destinations}
        top_journey_destinations = sorted(all_journey_dests.items(), key=lambda x: x[1], reverse=True)[:10]

        # Assess maturity
        total_items = len(journeys)
        active_items = len(active_journeys) + len(active_campaigns)
        draft_items = len(draft_journeys) + len(draft_campaigns)

        maturity_level = "none"
        if active_items > 5:
            maturity_level = "advanced"
        elif active_items > 0:
            maturity_level = "emerging"
        elif draft_items > 0:
            maturity_level = "exploring"

        # Group by space
        journeys_by_space = {}
        for journey in journeys:
            space = journey.get('Space', 'Unknown')
            if space not in journeys_by_space:
                journeys_by_space[space] = []
            journeys_by_space[space].append({
                'name': journey.get('Name', ''),
                'type': journey.get('Type', ''),
                'state': journey.get('State', ''),
                'status': journey.get('Status', '')
            })

        return {
            "has_journeys": True,
            "total_items": total_items,
            "journeys": {
                "total": len(journey_items),
                "active": len(active_journeys),
                "draft": len(draft_journeys),
                "published": len(published_journeys)
            },
            "campaigns": {
                "total": len(campaign_items),
                "active": len(active_campaigns),
                "draft": len(draft_campaigns)
            },
            "destination_usage": {
                "journey_destinations": dict(sorted(journey_destinations.items(), key=lambda x: x[1], reverse=True)[:10]),
                "campaign_destinations": dict(sorted(campaign_destinations.items(), key=lambda x: x[1], reverse=True)[:10]),
                "top_orchestration_destinations": [{"name": name, "usage_count": count} for name, count in top_journey_destinations]
            },
            "maturity_assessment": {
                "level": maturity_level,
                "active_orchestrations": active_items,
                "draft_orchestrations": draft_items
            },
            "by_space": journeys_by_space
        }

    def _build_destination_summary(self, sources: List[Dict], audiences: List[Dict], destinations: Dict) -> Dict:
        """Summarize destination landscape with full destination data"""
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

        # Add from destinations JSON (full destination objects)
        destinations_list = destinations.get('destinations', [])
        destination_details = []
        for dest in destinations_list:
            dest_name = dest.get('name', '')
            if dest_name:
                all_destinations.add(dest_name)
                destination_details.append({
                    'name': dest_name,
                    'type': dest.get('__typename', 'Unknown'),
                    'enabled': dest.get('enabled', False),
                    'status': dest.get('integrationStatus') or dest.get('warehouseStatus'),
                    'categories': dest.get('metadata', {}).get('categories', [])
                })

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

    def _build_profile_insights_summary(self, profile_insights: List[Dict], space_sources: List[Dict]) -> Dict:
        """
        Summarize identity resolution configurations and space-source mappings
        Critical for understanding data flow: which sources feed which spaces
        """
        if not profile_insights and not space_sources:
            return {
                "has_profile_resolution": False,
                "message": "No identity resolution configured"
            }

        # Group profile configs by space
        configs_by_space = {}
        for config in profile_insights:
            space_slug = config.get('Space Slug', '')
            space_name = config.get('Space Name', '')

            if space_slug not in configs_by_space:
                configs_by_space[space_slug] = {
                    "space_name": space_name,
                    "space_slug": space_slug,
                    "identity_types": [],
                    "optional_identity_types": [],
                    "profile_limit": config.get('Profile Limit'),
                    "merge_protection": config.get('Merge Protection Enabled', '').lower() == 'true'
                }

            # Collect identity types
            id_type = config.get('Identity Type', '')
            if id_type:
                if config.get('Optional', '').lower() == 'true':
                    configs_by_space[space_slug]["optional_identity_types"].append(id_type)
                else:
                    configs_by_space[space_slug]["identity_types"].append(id_type)

        # Map sources to spaces
        source_space_map = {}
        for mapping in space_sources:
            source_name = mapping.get('Source Name', '')
            space_slug = mapping.get('Space Slug', '')
            space_name = mapping.get('Space Name', '')

            if source_name:
                if source_name not in source_space_map:
                    source_space_map[source_name] = []
                source_space_map[source_name].append({
                    "space_slug": space_slug,
                    "space_name": space_name
                })

        # Build maturity assessment
        total_spaces = len(configs_by_space)
        spaces_with_email = sum(1 for cfg in configs_by_space.values()
                                if 'email' in [t.lower() for t in cfg['identity_types']])
        spaces_with_multiple_ids = sum(1 for cfg in configs_by_space.values()
                                       if len(cfg['identity_types']) > 1)

        maturity_level = "basic"
        if spaces_with_multiple_ids > 0 and spaces_with_email > 0:
            maturity_level = "advanced"
        elif spaces_with_email > 0 or spaces_with_multiple_ids > 0:
            maturity_level = "intermediate"

        return {
            "has_profile_resolution": True,
            "total_spaces_configured": total_spaces,
            "spaces": list(configs_by_space.values()),
            "source_to_space_mappings": source_space_map,
            "source_count": len(source_space_map),
            "maturity_assessment": {
                "level": maturity_level,
                "spaces_with_email_resolution": spaces_with_email,
                "spaces_with_multi_id_resolution": spaces_with_multiple_ids
            },
            "data_flow_insights": {
                "sources_feeding_profiles": len(source_space_map),
                "total_data_pathways": sum(len(spaces) for spaces in source_space_map.values())
            }
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
