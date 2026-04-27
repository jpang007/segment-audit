#!/usr/bin/env python3
"""
Recommendations Engine - Rule-based workspace analysis
GATEWAY API ONLY - Uses only gateway_* files from Gateway API
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class RecommendationsEngine:
    """Analyzes Gateway API audit data and generates actionable recommendations"""

    SEVERITY_HIGH = "high"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_LOW = "low"

    def __init__(self, audit_data_dir: Path):
        self.data_dir = Path(audit_data_dir)
        self.findings = []

    def analyze(self) -> Dict[str, Any]:
        """Run all analysis rules and return structured findings"""
        self.findings = []

        # Load all Gateway API data files
        data = self._load_gateway_data()

        if not data:
            return {"error": "No Gateway API audit data found", "findings": []}

        # Run analysis rules
        self._analyze_activation_gaps(data)
        self._analyze_underutilized_sources(data)
        self._analyze_stale_audiences(data)
        self._analyze_audience_health(data)

        # Sort by severity
        priority_order = {self.SEVERITY_HIGH: 0, self.SEVERITY_MEDIUM: 1, self.SEVERITY_LOW: 2}
        self.findings.sort(key=lambda x: priority_order.get(x['severity'], 3))

        return {
            "workspace": data.get('summary', {}).get('workspace_slug', 'Unknown'),
            "workspace_name": data.get('summary', {}).get('customer_name', 'Unknown'),
            "analysis_date": datetime.now().isoformat(),
            "total_findings": len(self.findings),
            "high_priority": len([f for f in self.findings if f['severity'] == self.SEVERITY_HIGH]),
            "medium_priority": len([f for f in self.findings if f['severity'] == self.SEVERITY_MEDIUM]),
            "low_priority": len([f for f in self.findings if f['severity'] == self.SEVERITY_LOW]),
            "findings": self.findings
        }

    def _load_gateway_data(self) -> Dict[str, Any]:
        """Load Gateway API audit data files ONLY"""
        data = {}

        # Load Gateway summary
        summary_file = self.data_dir / 'gateway_summary.json'
        if summary_file.exists():
            with open(summary_file) as f:
                data['summary'] = json.load(f)
        else:
            print("⚠️  WARNING: gateway_summary.json not found")
            return {}

        # Load Gateway sources
        sources_file = self.data_dir / 'gateway_sources.csv'
        if sources_file.exists():
            data['sources'] = self._load_csv(sources_file)
            print(f"✓ Loaded {len(data['sources'])} sources from Gateway API")
        else:
            print("⚠️  WARNING: gateway_sources.csv not found")
            data['sources'] = []

        # Load Gateway audiences
        audiences_file = self.data_dir / 'gateway_audiences.csv'
        if audiences_file.exists():
            data['audiences'] = self._load_csv(audiences_file)
            print(f"✓ Loaded {len(data['audiences'])} audiences from Gateway API")
        else:
            print("⚠️  WARNING: gateway_audiences.csv not found")
            data['audiences'] = []

        return data

    def _load_csv(self, file_path: Path) -> List[Dict[str, str]]:
        """Load CSV file and return list of dicts"""
        rows = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
        return rows

    def _analyze_activation_gaps(self, data: Dict[str, Any]):
        """Find audiences with users but no destinations (Gateway API format)"""
        audiences = data.get('audiences', [])
        if not audiences:
            return

        # Gateway columns: Enabled, Size, Destination Count
        unactivated = []
        total_users = 0

        for aud in audiences:
            enabled = aud.get('Enabled', '').lower() == 'true'
            size_str = aud.get('Size', '0')
            dest_count_str = aud.get('Destination Count', '0')

            # Parse size
            try:
                size = int(size_str.replace(',', '')) if size_str and size_str not in ['Computing...', ''] else 0
            except (ValueError, AttributeError):
                size = 0

            # Parse destination count
            try:
                dest_count = int(dest_count_str) if dest_count_str else 0
            except (ValueError, AttributeError):
                dest_count = 0

            if enabled and size > 0 and dest_count == 0:
                unactivated.append({
                    'name': aud.get('Name', ''),
                    'id': aud.get('ID', ''),
                    'size': size,
                    'space': aud.get('Space', '')
                })
                total_users += size

        if unactivated:
            # Get top 5 by size
            top_5 = sorted(unactivated, key=lambda x: x['size'], reverse=True)[:5]
            top_items = ', '.join([f"{a['name']} ({a['size']:,} users)" for a in top_5[:3]])

            self.findings.append({
                'type': 'activation_gap',
                'severity': self.SEVERITY_HIGH,
                'title': 'Audiences Not Activated',
                'evidence': f"{len(unactivated)} enabled audiences have users but no connected destinations",
                'impact': f"Potential reach of {total_users:,} users not being utilized for campaigns",
                'recommendation': f"Connect these audiences to downstream destinations like Braze, Iterable, Google Ads. Top audiences: {top_items}",
                'affected_items': [a['name'] for a in top_5[:10]],
                'count': len(unactivated),
                'data_source': 'Gateway API'
            })

    def _analyze_underutilized_sources(self, data: Dict[str, Any]):
        """Find enabled sources with no or few destinations (Gateway API format)"""
        sources = data.get('sources', [])
        if not sources:
            return

        # Gateway columns: Status, Connected Destinations
        underutilized = []

        for src in sources:
            status = src.get('Status', '')
            destinations = src.get('Connected Destinations', '')
            dest_count = len(destinations.split(',')) if destinations and destinations.strip() else 0

            if status == 'ENABLED' and dest_count == 0:
                underutilized.append({
                    'name': src.get('Name', ''),
                    'id': src.get('ID', ''),
                    'type': src.get('Type', ''),
                    'dest_count': dest_count
                })

        if underutilized:
            top_items = ', '.join([f"{s['name']} ({s['type']})" for s in underutilized[:3]])

            self.findings.append({
                'type': 'underutilized_source',
                'severity': self.SEVERITY_MEDIUM,
                'title': 'Sources Not Connected to Destinations',
                'evidence': f"{len(underutilized)} enabled sources have no destination connections",
                'impact': "Data being collected but not flowing to activation tools or warehouses",
                'recommendation': f"Connect sources to destinations or disable if unused. Examples: {top_items}",
                'affected_items': [s['name'] for s in underutilized[:10]],
                'count': len(underutilized),
                'data_source': 'Gateway API'
            })

    def _analyze_stale_audiences(self, data: Dict[str, Any]):
        """Find empty or disabled audiences (Gateway API format)"""
        audiences = data.get('audiences', [])
        if not audiences:
            return

        empty_enabled = []
        disabled_with_users = []

        for aud in audiences:
            enabled = aud.get('Enabled', '').lower() == 'true'
            size_str = aud.get('Size', '0')

            try:
                size = int(size_str.replace(',', '')) if size_str and size_str not in ['Computing...', ''] else 0
            except (ValueError, AttributeError):
                size = 0

            if enabled and size == 0:
                empty_enabled.append({
                    'name': aud.get('Name', ''),
                    'id': aud.get('ID', ''),
                    'space': aud.get('Space', '')
                })
            elif not enabled and size > 1000:
                disabled_with_users.append({
                    'name': aud.get('Name', ''),
                    'id': aud.get('ID', ''),
                    'size': size,
                    'space': aud.get('Space', '')
                })

        if empty_enabled:
            top_items = ', '.join([a['name'] for a in empty_enabled[:5]])
            self.findings.append({
                'type': 'stale_audience',
                'severity': self.SEVERITY_LOW,
                'title': 'Empty Enabled Audiences',
                'evidence': f"{len(empty_enabled)} enabled audiences have 0 users",
                'impact': "Workspace clutter, wasted computation resources",
                'recommendation': f"Review logic or delete unused audiences. Examples: {top_items}",
                'affected_items': [a['name'] for a in empty_enabled[:20]],
                'count': len(empty_enabled),
                'data_source': 'Gateway API'
            })

        if disabled_with_users:
            total_users = sum(a['size'] for a in disabled_with_users)
            top_items = ', '.join([f"{a['name']} ({a['size']:,} users)" for a in disabled_with_users[:3]])
            self.findings.append({
                'type': 'workspace_hygiene',
                'severity': self.SEVERITY_MEDIUM,
                'title': 'Disabled Audiences with Users',
                'evidence': f"{len(disabled_with_users)} disabled audiences still have {total_users:,} users",
                'impact': "Potential audience re-activation opportunities or cleanup needed",
                'recommendation': f"Re-enable valuable audiences or delete if truly unused. Examples: {top_items}",
                'affected_items': [a['name'] for a in disabled_with_users[:10]],
                'count': len(disabled_with_users),
                'data_source': 'Gateway API'
            })

    def _analyze_audience_health(self, data: Dict[str, Any]):
        """Analyze overall audience health (Gateway API format)"""
        audiences = data.get('audiences', [])
        if not audiences:
            return

        enabled_count = 0
        with_users = 0
        with_destinations = 0
        total_users = 0

        for aud in audiences:
            enabled = aud.get('Enabled', '').lower() == 'true'
            size_str = aud.get('Size', '0')
            dest_count_str = aud.get('Destination Count', '0')

            try:
                size = int(size_str.replace(',', '')) if size_str and size_str not in ['Computing...', ''] else 0
            except (ValueError, AttributeError):
                size = 0

            try:
                dest_count = int(dest_count_str) if dest_count_str else 0
            except (ValueError, AttributeError):
                dest_count = 0

            if enabled:
                enabled_count += 1
                if size > 0:
                    with_users += 1
                    total_users += size
                if dest_count > 0:
                    with_destinations += 1

        activation_rate = (with_destinations / enabled_count * 100) if enabled_count > 0 else 0

        if activation_rate < 50:
            self.findings.append({
                'type': 'activation_gap',
                'severity': self.SEVERITY_HIGH,
                'title': 'Low Audience Activation Rate',
                'evidence': f"Only {activation_rate:.1f}% of enabled audiences are connected to destinations ({with_destinations}/{enabled_count})",
                'impact': f"{total_users:,} total users across {with_users} audiences, but low activation",
                'recommendation': "Prioritize connecting high-value audiences to marketing/analytics platforms",
                'affected_items': [],
                'count': enabled_count - with_destinations,
                'data_source': 'Gateway API'
            })


def generate_recommendations(audit_data_dir: str = './audit_data') -> Dict[str, Any]:
    """
    Main entry point for generating recommendations
    Uses ONLY Gateway API data files
    """
    print("\n" + "="*70)
    print("🔍 GATEWAY API RECOMMENDATIONS ENGINE")
    print("="*70)
    print(f"📁 Data directory: {audit_data_dir}")
    print(f"📊 Using ONLY Gateway API files (gateway_*.csv/json)")
    print("="*70 + "\n")

    engine = RecommendationsEngine(Path(audit_data_dir))
    results = engine.analyze()

    print("\n" + "="*70)
    print(f"✅ Analysis Complete")
    print(f"   Total Findings: {results.get('total_findings', 0)}")
    print(f"   High Priority: {results.get('high_priority', 0)}")
    print(f"   Medium Priority: {results.get('medium_priority', 0)}")
    print(f"   Low Priority: {results.get('low_priority', 0)}")
    print("="*70 + "\n")

    return results


# CLI usage
if __name__ == '__main__':
    import sys
    audit_dir = sys.argv[1] if len(sys.argv) > 1 else './audit_data'
    results = generate_recommendations(audit_dir)
    print(json.dumps(results, indent=2))
