#!/usr/bin/env python3
"""
Segment Audit Dashboard - Integrated Flask App
Single app with form input + visual dashboard
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import os
import json
import threading
import time
from pathlib import Path
from datetime import datetime
import requests
from collections import Counter

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Configuration
DATA_DIR = Path('./audit_data')
DATA_DIR.mkdir(exist_ok=True)

UPLOAD_DIR = Path('./uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

# Global status for audit progress
audit_status = {
    'running': False,
    'progress': 0,
    'message': 'Ready',
    'complete': False,
    'error': None
}

# ============================================================================
# DATA COLLECTION (from segment_audit_collector.py)
# ============================================================================

class SegmentAuditor:
    """Collects Segment workspace data"""

    def __init__(self, api_token, workspace_id=None, space_id=None, skip_ssl_verify=False):
        self.api_token = api_token
        self.workspace_id = workspace_id
        self.space_id = space_id
        self.skip_ssl_verify = skip_ssl_verify
        self.verify = not skip_ssl_verify  # If skip_ssl_verify=True, verify=False
        self.v1_base = "https://api.segmentapis.com"
        self.platform_base = "https://platform.segmentapis.com/v1beta"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        # Suppress SSL warnings if verification is disabled
        if skip_ssl_verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _paginate(self, url, data_key='data'):
        """Handle pagination"""
        all_data = []
        next_cursor = None

        while True:
            params = {'pagination.cursor': next_cursor, 'pagination.count': 200} if next_cursor else {'pagination.count': 200}

            # Retry logic for network issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=self.headers, params=params, timeout=30, verify=self.verify)
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        time.sleep(wait_time)
                        continue
                    else:
                        ssl_hint = " Try enabling 'Skip SSL Verification' checkbox if you're behind a VPN." if "SSL" in str(e) or "certificate" in str(e).lower() else ""
                        raise Exception(f"Network Error: Unable to connect to Segment API after {max_retries} attempts.{ssl_hint} Error: {str(e)}")

            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")

            data = response.json()
            data_wrapper = data.get(data_key, {})

            # Extract the actual items from the data wrapper
            if isinstance(data_wrapper, list):
                all_data.extend(data_wrapper)
                pagination = data.get('pagination', {})
            elif isinstance(data_wrapper, dict):
                # Find the list in the dict (e.g., 'audiences', 'sources')
                for key, value in data_wrapper.items():
                    if isinstance(value, list):
                        all_data.extend(value)
                        break
                # Pagination is inside the data wrapper
                pagination = data_wrapper.get('pagination', {})
            else:
                pagination = {}

            next_cursor = pagination.get('next')

            if not next_cursor:
                break

            time.sleep(0.3)

        return all_data

    def get_sources(self):
        """Get all sources"""
        url = f"{self.v1_base}/sources"
        return self._paginate(url, 'data')

    def get_source_destinations(self, source_id):
        """Get all destinations connected to a source"""
        url = f"{self.v1_base}/sources/{source_id}/connected-destinations"
        debug_file = Path('./audit_data/debug_destinations.txt')

        try:
            with open(debug_file, 'a') as f:
                f.write(f"\n\n=== Fetching destinations for source: {source_id} ===\n")
                f.write(f"URL: {url}\n")

            response = requests.get(url, headers=self.headers, timeout=30, verify=self.verify)

            with open(debug_file, 'a') as f:
                f.write(f"Response status: {response.status_code}\n")

            if response.status_code != 200:
                with open(debug_file, 'a') as f:
                    f.write(f"Non-200 response: {response.text[:500]}\n")
                return []

            data = response.json()
            with open(debug_file, 'a') as f:
                f.write(f"Response keys: {list(data.keys())}\n")
                f.write(f"Full response: {json.dumps(data, indent=2)[:1000]}\n")

            # API returns destinations in data.destinations
            destinations_wrapper = data.get('data', {})

            with open(debug_file, 'a') as f:
                f.write(f"destinations_wrapper type: {type(destinations_wrapper)}\n")
                if isinstance(destinations_wrapper, dict):
                    f.write(f"destinations_wrapper keys: {list(destinations_wrapper.keys())}\n")

            if isinstance(destinations_wrapper, dict):
                destinations = destinations_wrapper.get('destinations', [])
                with open(debug_file, 'a') as f:
                    f.write(f"Found {len(destinations)} destinations\n")
                return destinations
            return []
        except Exception as e:
            with open(debug_file, 'a') as f:
                f.write(f"ERROR: Exception fetching destinations: {str(e)}\n")
                import traceback
                f.write(traceback.format_exc())
            return []

    def get_workspace(self):
        """Get workspace information from token"""
        # Try multiple possible endpoints
        possible_endpoints = [
            f"{self.v1_base}/workspace",
            f"{self.v1_base}/workspaces",
            f"{self.v1_base}",
            f"{self.v1_base}/"
        ]

        last_error = None
        for url in possible_endpoints:
            try:
                response = requests.get(url, headers=self.headers, timeout=30, verify=self.verify)
                if response.status_code == 200:
                    data = response.json()
                    # Try different response structures
                    workspace = data.get('data', {}).get('workspace', {})
                    if not workspace:
                        workspace = data.get('workspace', {})
                    if not workspace and 'id' in data:
                        workspace = data
                    if workspace and 'id' in workspace:
                        return workspace
                last_error = f"{response.status_code} - {response.text[:200]}"
            except Exception as e:
                last_error = str(e)
                continue

        raise Exception(f"Could not fetch workspace info. Last error: {last_error}")

    def get_spaces(self):
        """Get all spaces in the workspace"""
        url = f"{self.v1_base}/spaces"
        return self._paginate(url, 'data')

    def get_audiences(self):
        """Get all audiences"""
        if not self.space_id:
            return []
        url = f"{self.v1_base}/spaces/{self.space_id}/audiences"
        return self._paginate(url, 'data')

    def get_event_volumes(self, start_time, end_time, granularity='DAY', group_by=None):
        """Get event volumes for workspace"""
        url = f"{self.v1_base}/events/volume"

        params = {
            'granularity': granularity,
            'startTime': start_time,
            'endTime': end_time
        }

        # Add groupBy if specified (e.g., ['eventType', 'sourceId'])
        if group_by:
            for i, group in enumerate(group_by):
                params[f'groupBy.{i}'] = group

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30, verify=self.verify)
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            return response.json()
        except Exception as e:
            raise Exception(f"Error fetching event volumes: {str(e)}")

    def extract_events_and_traits(self, definition):
        """Extract event and trait names from audience definition"""
        import re
        events = set()
        traits = set()

        # Parse query string if it exists
        if isinstance(definition, dict) and 'query' in definition:
            query = definition.get('query', '')

            # Extract events: event('Event Name')
            event_matches = re.findall(r"event\(['\"]([^'\"]+)['\"]\)", query)
            events.update(event_matches)

            # Extract traits: trait('trait_name')
            trait_matches = re.findall(r"trait\(['\"]([^'\"]+)['\"]\)", query)
            traits.update(trait_matches)

        # Also traverse the definition object for structured format
        def traverse(obj):
            if isinstance(obj, dict):
                if 'event' in obj:
                    event_obj = obj['event']
                    if isinstance(event_obj, dict) and 'name' in event_obj:
                        events.add(event_obj['name'])
                    elif isinstance(event_obj, str):
                        events.add(event_obj)

                if 'trait' in obj:
                    trait_obj = obj['trait']
                    if isinstance(trait_obj, dict) and 'name' in trait_obj:
                        traits.add(trait_obj['name'])
                    elif isinstance(trait_obj, str):
                        traits.add(trait_obj)

                for value in obj.values():
                    traverse(value)
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item)

        traverse(definition)
        return events, traits

def run_audit(api_token, workspace_slug_fallback=None, skip_ssl_verify=False):
    """Run the audit in background thread"""
    global audit_status

    try:
        audit_status = {
            'running': True,
            'progress': 3,
            'message': 'Fetching workspace information...',
            'complete': False,
            'error': None
        }

        # Try to fetch workspace info from token
        auditor = SegmentAuditor(api_token, skip_ssl_verify=skip_ssl_verify)

        try:
            workspace = auditor.get_workspace()
            workspace_id = workspace.get('id')
            workspace_slug = workspace.get('slug', workspace.get('name'))
            workspace_name = workspace.get('display_name', workspace.get('name', workspace_slug))

            audit_status['progress'] = 5
            audit_status['message'] = f'Found workspace: {workspace_name}. Fetching spaces...'
        except Exception as e:
            # Fallback to manual slug if provided
            if workspace_slug_fallback:
                workspace_id = None
                workspace_slug = workspace_slug_fallback
                workspace_name = workspace_slug.replace('-', ' ').replace('_', ' ').title()
                audit_status['progress'] = 5
                audit_status['message'] = f'Using workspace: {workspace_name} (manual). Fetching spaces...'
            else:
                raise Exception(f"Could not fetch workspace info and no workspace slug provided. Error: {str(e)}")

        # Fetch all spaces automatically
        spaces = auditor.get_spaces()
        space_list = [space.get('id') for space in spaces if space.get('id')]

        # Create space mapping (ID -> Name) for better readability
        space_mapping = {space.get('id'): space.get('name', space.get('id')) for space in spaces if space.get('id')}

        if not space_list:
            raise Exception("No spaces found in workspace. Make sure your workspace has the Spaces feature enabled.")

        audit_status['progress'] = 10
        audit_status['message'] = f'Found {len(space_list)} space(s). Connecting to Segment API...'

        all_audiences = []
        all_events = Counter()
        all_traits = Counter()
        sources_data = []

        # Collect sources (always - API token is workspace-scoped)
        audit_status['message'] = 'Collecting source data...'
        audit_status['progress'] = 20

        auditor = SegmentAuditor(api_token, workspace_id=workspace_id, skip_ssl_verify=skip_ssl_verify)
        sources = auditor.get_sources()

        for idx, source in enumerate(sources):
            metadata = source.get('metadata', {})
            source_type = metadata.get('name', 'Unknown')

            # Skip Personas sources (Segment-generated)
            if source_type == 'Personas':
                continue

            categories = metadata.get('categories', [])
            # Use first category as the type (e.g., "Website" instead of "Javascript")
            category_type = categories[0] if categories and len(categories) > 0 else source_type
            write_keys = source.get('writeKeys', [])
            labels = source.get('labels', [])

            # Get connected destinations for this source
            audit_status['message'] = f'Collecting destinations for source {idx+1}/{len(sources)}...'
            destinations_list = []
            destination_logos = {}
            try:
                source_id = source.get('id')
                destinations = auditor.get_source_destinations(source_id)

                for dest in destinations:
                    dest_name = dest.get('name', '')
                    dest_metadata = dest.get('metadata', {})
                    dest_slug = dest_metadata.get('slug', '')
                    dest_logo = dest_metadata.get('logos', {}).get('default', '')

                    if dest_slug:
                        destinations_list.append(dest_slug)
                        if dest_logo:
                            destination_logos[dest_slug] = dest_logo
            except Exception as e:
                # If fetching destinations fails, continue with empty list
                pass

            # Ensure all items are strings
            categories_str = ', '.join(str(c) for c in categories) if categories else 'Unknown'
            write_keys_str = ', '.join(str(w) for w in write_keys) if write_keys else ''
            # Labels might be dicts with 'key' field, or strings
            labels_str = ', '.join(
                label.get('key', str(label)) if isinstance(label, dict) else str(label)
                for label in labels
            ) if labels else ''
            destinations_str = ', '.join(destinations_list) if destinations_list else ''

            sources_data.append({
                'Source ID': source.get('id'),
                'Source Name': source.get('name'),
                'Slug': source.get('slug'),
                'Enabled': source.get('enabled', False),
                'Type': category_type,
                'Category': categories_str,
                'Write Keys': write_keys_str,
                'Labels': labels_str,
                'Connected Destinations': destinations_str,
                'Destination Count': len(destinations_list)
            })

        # Collect audiences from each space
        total_spaces = len(space_list)
        for idx, space_id in enumerate(space_list):
            audit_status['message'] = f'Collecting audiences from space {idx+1}/{total_spaces}...'
            audit_status['progress'] = 30 + (40 * idx // total_spaces)

            auditor = SegmentAuditor(api_token, space_id=space_id, skip_ssl_verify=skip_ssl_verify)
            audiences = auditor.get_audiences()

            for audience in audiences:
                # Extract size.count from size object
                size_obj = audience.get('size', {})
                size_count = size_obj.get('count', 0) if isinstance(size_obj, dict) else size_obj

                audience_data = {
                    'Enabled': audience.get('enabled', False),
                    'Name': audience.get('name'),
                    'Key': audience.get('key'),
                    'Size': size_count,
                    'Description': audience.get('description', ''),
                    'Created By': audience.get('createdBy', ''),
                    'Created At': audience.get('createdAt', ''),
                    'Updated At': audience.get('updatedAt', ''),
                    'Space ID': space_id
                }
                all_audiences.append(audience_data)

                # Extract events and traits
                definition = audience.get('definition', {})
                events, traits = auditor.extract_events_and_traits(definition)

                for event in events:
                    all_events[event] += 1
                for trait in traits:
                    all_traits[trait] += 1

        # Save data files
        audit_status['message'] = 'Saving audit data...'
        audit_status['progress'] = 80

        # Save summary
        # Use workspace display name (already formatted nicely from API)
        display_name = workspace_name

        # Store workspace info in session for dashboard views
        # Note: session updates must happen in request context, so we'll update via global
        audit_status['workspace_info'] = {
            'customer_name': display_name,
            'workspace_slug': workspace_slug,
            'workspace_id': workspace_id
        }

        summary = {
            'audit_date': datetime.now().isoformat(),
            'customer_name': display_name,
            'workspace_id': workspace_id,
            'workspace_slug': workspace_slug,
            'space_ids': space_list,
            'space_mapping': space_mapping,  # ID -> Name mapping
            'sources': {
                'total': len(sources_data),
                'enabled': len([s for s in sources_data if s['Enabled']]),
                'disabled': len([s for s in sources_data if not s['Enabled']])
            },
            'audiences': {
                'total': len(all_audiences),
                'enabled': len([a for a in all_audiences if a['Enabled']]),
                'disabled': len([a for a in all_audiences if not a['Enabled']]),
                'empty': len([a for a in all_audiences if a['Size'] == 0])
            },
            'coverage': {
                'unique_events_referenced': len(all_events),
                'unique_traits_referenced': len(all_traits),
                'top_events': dict(all_events.most_common(10)),
                'top_traits': dict(all_traits.most_common(10))
            }
        }

        with open(DATA_DIR / 'audit_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        # Save CSVs
        import csv

        # Audiences
        if all_audiences:
            with open(DATA_DIR / 'segment_audiences_audit.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_audiences[0].keys())
                writer.writeheader()
                writer.writerows(all_audiences)

        # Events
        with open(DATA_DIR / 'event_coverage.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Event', 'Audience Uses'])
            for event, count in all_events.most_common():
                writer.writerow([event, count])

        # Traits
        with open(DATA_DIR / 'trait_coverage.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Trait', 'Audience Uses'])
            for trait, count in all_traits.most_common():
                writer.writerow([trait, count])

        # Sources
        if sources_data:
            with open(DATA_DIR / 'segment_sources_audit.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sources_data[0].keys())
                writer.writeheader()
                writer.writerows(sources_data)

        audit_status['message'] = 'Audit complete!'
        audit_status['progress'] = 100
        audit_status['complete'] = True
        audit_status['running'] = False

    except Exception as e:
        audit_status['running'] = False
        audit_status['error'] = str(e)
        audit_status['message'] = f'Error: {str(e)}'
        audit_status['complete'] = False

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page with configuration form"""
    return render_template('index.html')

@app.route('/run-audit', methods=['POST'])
def run_audit_route():
    """Start audit data collection"""
    global audit_status

    if audit_status['running']:
        return jsonify({'error': 'Audit already running'}), 400

    # Get form data
    api_token = request.form.get('api_token')
    workspace_slug = request.form.get('workspace_slug', '').strip()
    skip_ssl = request.form.get('skip_ssl') == 'true'  # Checkbox returns 'true' or None

    # Validate
    if not api_token:
        return jsonify({'error': 'API token is required'}), 400

    # Store credentials in session for later use (workspace details will be fetched during audit)
    session['api_token'] = api_token
    session['skip_ssl'] = skip_ssl

    # Reset status
    audit_status = {
        'running': True,
        'progress': 0,
        'message': 'Starting audit...',
        'complete': False,
        'error': None
    }

    # Run audit in background thread (everything will be fetched automatically from token)
    thread = threading.Thread(
        target=run_audit,
        args=(api_token, workspace_slug if workspace_slug else None, skip_ssl)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'redirect': '/progress'})

@app.route('/progress')
def progress():
    """Progress page showing audit status"""
    return render_template('progress.html')

@app.route('/api/status')
def status():
    """API endpoint for audit status"""
    # If audit is complete and workspace info is available, update session
    if audit_status.get('complete') and 'workspace_info' in audit_status:
        workspace_info = audit_status['workspace_info']
        session['customer_name'] = workspace_info['customer_name']
        session['workspace_slug'] = workspace_info['workspace_slug']
        session['workspace_id'] = workspace_info['workspace_id']

    return jsonify(audit_status)

@app.route('/api/list-spaces', methods=['POST'])
def list_spaces():
    """Fetch all spaces for a given API token"""
    try:
        data = request.get_json()
        api_token = data.get('api_token')
        skip_ssl = data.get('skip_ssl', False)

        if not api_token:
            return jsonify({'error': 'API token is required'}), 400

        auditor = SegmentAuditor(api_token, skip_ssl_verify=skip_ssl)
        spaces = auditor.get_spaces()

        # Format spaces for response
        spaces_list = []
        for space in spaces:
            spaces_list.append({
                'id': space.get('id'),
                'name': space.get('name'),
                'slug': space.get('slug', '')
            })

        return jsonify({'spaces': spaces_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Main dashboard view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('dashboard.html', customer_name=customer_name)

@app.route('/sources')
def sources():
    """Sources view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('sources.html', customer_name=customer_name)

@app.route('/observability')
def observability():
    """Observability view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('observability.html', customer_name=customer_name)

@app.route('/connections')
def connections():
    """Connections view - Sankey diagram of source to destination flows"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('connections.html', customer_name=customer_name)

@app.route('/export-workspace-markdown')
def export_workspace_markdown():
    """Export comprehensive workspace data as markdown for AI analysis"""
    from io import BytesIO

    workspace_slug = session.get('workspace_slug', 'workspace')
    customer_name = session.get('customer_name', workspace_slug)

    # Load all data files
    summary_file = DATA_DIR / 'audit_summary.json'
    sources_file = DATA_DIR / 'segment_sources_audit.csv'
    audiences_file = DATA_DIR / 'segment_audiences_audit.csv'

    if not summary_file.exists():
        return "No audit data found. Please run an audit first.", 404

    # Load summary
    with open(summary_file, 'r') as f:
        summary = json.load(f)

    # Load sources
    import csv
    sources = []
    if sources_file.exists():
        with open(sources_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            sources = list(reader)

    # Load audiences
    audiences = []
    if audiences_file.exists():
        with open(audiences_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            audiences = list(reader)

    # Build markdown content
    audit_date = summary.get('audit_date', '')
    if audit_date:
        from datetime import datetime
        audit_date_obj = datetime.fromisoformat(audit_date)
        audit_date = audit_date_obj.strftime('%B %d, %Y at %I:%M %p')

    md_content = f"""# {customer_name} - Segment Workspace Analysis

## Executive Summary

**Audit Date:** {audit_date}
**Workspace:** {workspace_slug}
**Total Sources:** {summary.get('sources', {}).get('total', 0)} ({summary.get('sources', {}).get('enabled', 0)} enabled)
**Total Audiences:** {summary.get('audiences', {}).get('total', 0)} ({summary.get('audiences', {}).get('enabled', 0)} enabled)
**Unique Events Referenced:** {summary.get('coverage', {}).get('unique_events_referenced', 0)}
**Unique Traits Referenced:** {summary.get('coverage', {}).get('unique_traits_referenced', 0)}

---

## Workspace Overview

This workspace contains **{len(sources)} data sources** collecting customer data and sending it to various destinations. The workspace is configured with **{len(audiences)} audiences** for customer segmentation and targeting.

### Key Metrics
- **Active Sources:** {summary.get('sources', {}).get('enabled', 0)} sources actively collecting data
- **Inactive Sources:** {summary.get('sources', {}).get('disabled', 0)} sources currently disabled
- **Active Audiences:** {summary.get('audiences', {}).get('enabled', 0)} audiences currently enabled
- **Empty Audiences:** {summary.get('audiences', {}).get('empty', 0)} audiences with no users

---

## Data Sources

### Sources by Type
"""

    # Group sources by type
    from collections import Counter
    source_types = Counter()
    source_categories = Counter()
    enabled_by_type = Counter()

    for source in sources:
        source_type = source.get('Type', 'Unknown')
        enabled = source.get('Enabled', '').lower() == 'true'
        source_types[source_type] += 1
        if enabled:
            enabled_by_type[source_type] += 1

    for source_type, count in source_types.most_common():
        enabled_count = enabled_by_type.get(source_type, 0)
        md_content += f"\n- **{source_type}:** {count} total ({enabled_count} enabled)"

    md_content += "\n\n### Active Data Collection Sources\n"
    md_content += "\nThese sources are actively collecting customer data:\n\n"

    enabled_sources = [s for s in sources if s.get('Enabled', '').lower() == 'true']
    for source in enabled_sources:
        source_name = source.get('Source Name', '')
        source_type = source.get('Type', '')
        destinations = source.get('Connected Destinations', 'None')
        dest_count = source.get('Destination Count', '0')

        md_content += f"#### {source_name}\n"
        md_content += f"- **Type:** {source_type}\n"
        md_content += f"- **Connected Destinations ({dest_count}):** {destinations}\n"

        # Add source link if available
        source_slug = source.get('Slug', '')
        if workspace_slug and source_slug:
            md_content += f"- **Schema Link:** https://app.segment.com/{workspace_slug}/sources/{source_slug}/schema\n"

        md_content += "\n"

    md_content += "\n---\n\n## Destination Connections\n\n"
    md_content += "### Data Flow Summary\n\n"

    # Collect all unique destinations
    all_destinations = Counter()
    for source in sources:
        destinations = source.get('Connected Destinations', '').split(',')
        for dest in destinations:
            dest = dest.strip()
            if dest:
                all_destinations[dest] += 1

    md_content += "The following destinations are receiving data from this workspace:\n\n"
    for dest, count in all_destinations.most_common():
        md_content += f"- **{dest}:** Connected to {count} source(s)\n"

    md_content += "\n---\n\n## Audience Segments\n\n"
    md_content += f"This workspace has **{len(audiences)} audience segments** defined for user targeting and personalization.\n\n"

    # Group audiences by status
    enabled_audiences = [a for a in audiences if a.get('Enabled', '').lower() == 'true']

    md_content += f"### Active Audiences ({len(enabled_audiences)})\n\n"

    for audience in sorted(enabled_audiences, key=lambda x: int(x.get('Size', 0) or 0), reverse=True)[:20]:
        aud_name = audience.get('Name', '')
        aud_size = audience.get('Size', '0')
        aud_desc = audience.get('Description', 'No description')

        md_content += f"#### {aud_name}\n"
        md_content += f"- **Size:** {int(aud_size):,} users\n"
        md_content += f"- **Description:** {aud_desc}\n"
        md_content += "\n"

    if len(enabled_audiences) > 20:
        md_content += f"\n_...and {len(enabled_audiences) - 20} more active audiences_\n"

    md_content += "\n---\n\n## Event & Trait Coverage\n\n"
    md_content += "### Top Events Referenced in Audiences\n\n"

    top_events = summary.get('coverage', {}).get('top_events', {})
    if top_events:
        for event, count in list(top_events.items())[:10]:
            md_content += f"- **{event}:** Used in {count} audience(s)\n"

    md_content += "\n### Top Traits Referenced in Audiences\n\n"

    top_traits = summary.get('coverage', {}).get('top_traits', {})
    if top_traits:
        for trait, count in list(top_traits.items())[:10]:
            md_content += f"- **{trait}:** Used in {count} audience(s)\n"

    md_content += "\n---\n\n## Use Case Analysis\n\n"
    md_content += "### Inferred Use Cases\n\n"

    # Infer use cases based on destinations
    use_cases = []

    if any('amplitude' in d.lower() for d in all_destinations.keys()):
        use_cases.append("**Product Analytics:** Using Amplitude for product usage analysis and user behavior tracking")

    if any('google-analytics' in d.lower() or 'ga4' in d.lower() for d in all_destinations.keys()):
        use_cases.append("**Web Analytics:** Using Google Analytics for website traffic and conversion tracking")

    if any('hubspot' in d.lower() or 'salesforce' in d.lower() for d in all_destinations.keys()):
        use_cases.append("**CRM Integration:** Syncing customer data to CRM systems for sales and marketing")

    if any('klaviyo' in d.lower() or 'braze' in d.lower() or 'iterable' in d.lower() for d in all_destinations.keys()):
        use_cases.append("**Email Marketing:** Powering personalized email campaigns and lifecycle messaging")

    if any('facebook' in d.lower() or 'google-ads' in d.lower() or 'adwords' in d.lower() for d in all_destinations.keys()):
        use_cases.append("**Paid Advertising:** Syncing audiences to advertising platforms for targeted campaigns")

    if any('redshift' in d.lower() or 'bigquery' in d.lower() or 'snowflake' in d.lower() for d in all_destinations.keys()):
        use_cases.append("**Data Warehousing:** Storing raw event data for custom analysis and reporting")

    if any('s3' in d.lower() or 'gcs' in d.lower() for d in all_destinations.keys()):
        use_cases.append("**Data Lake:** Archiving raw data for long-term storage and compliance")

    for use_case in use_cases:
        md_content += f"- {use_case}\n"

    if not use_cases:
        md_content += "- Based on destination configuration, this workspace appears to be used for general customer data collection and routing.\n"

    md_content += "\n### Data Collection Strategy\n\n"

    website_sources = len([s for s in sources if s.get('Type') == 'Website'])
    server_sources = len([s for s in sources if s.get('Type') == 'Server'])
    mobile_sources = len([s for s in sources if 'mobile' in s.get('Type', '').lower() or 'ios' in s.get('Type', '').lower() or 'android' in s.get('Type', '').lower()])

    if website_sources > 0:
        md_content += f"- **Web Tracking:** {website_sources} website source(s) tracking user behavior on web properties\n"
    if server_sources > 0:
        md_content += f"- **Server-Side Tracking:** {server_sources} server source(s) for backend event collection\n"
    if mobile_sources > 0:
        md_content += f"- **Mobile Tracking:** {mobile_sources} mobile app source(s) for iOS/Android tracking\n"

    md_content += "\n---\n\n## Recommendations for AI Analysis\n\n"
    md_content += """When analyzing this workspace, consider:

1. **Data Flow Patterns:** Examine which sources feed into which destinations to understand data routing
2. **Audience Strategy:** Review audience definitions and sizes to understand segmentation approach
3. **Event Coverage:** Look at which events are most frequently used in audiences to identify key behaviors
4. **Use Case Alignment:** Evaluate if the current setup aligns with stated business objectives
5. **Data Quality:** Check for empty audiences, disabled sources, or unused connections that may indicate data quality issues
6. **Scaling Opportunities:** Identify underutilized destinations or audience patterns that could be expanded

---

## Additional Context

This markdown file was generated from a Segment workspace audit and is optimized for AI analysis. You can use this data to:

- Understand the current state of data collection and routing
- Identify optimization opportunities
- Plan migrations or architecture changes
- Document the workspace for stakeholders
- Generate insights about user behavior and segmentation strategies

For more detailed analysis, consider reviewing the source schemas directly in Segment or examining raw event data in your data warehouse.
"""

    # Create response
    output = BytesIO(md_content.encode('utf-8'))
    output.seek(0)

    from flask import send_file
    return send_file(
        output,
        mimetype='text/markdown',
        as_attachment=True,
        download_name=f'{customer_name}_workspace_analysis.md'
    )

@app.route('/export-workspace-analysis')
def export_workspace_analysis():
    """Export sources data in Workspace Analysis format (Excel)"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, colors
    from openpyxl.styles.borders import Border, Side
    from io import BytesIO

    workspace_slug = session.get('workspace_slug', 'workspace')
    customer_name = session.get('customer_name', workspace_slug)

    # Load sources data
    sources_file = DATA_DIR / 'segment_sources_audit.csv'
    if not sources_file.exists():
        return "No sources data found. Please run an audit first.", 404

    import csv
    sources = []
    with open(sources_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sources = list(reader)

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Workspace Analysis"

    # Header styling
    header_fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)

    # Define headers matching template
    headers = [
        'Event Source Name',
        'Type',
        'Connection',
        'DEV / PROD',
        'Destinations Receiving',
        'Event Descriptions (Brief Summary) / Source Schema Link',
        'Use Case Notes'
    ]

    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(1, col, header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

    # Write data rows
    for row_idx, source in enumerate(sources, 2):
        # Event Source Name (with hyperlink if workspace slug available)
        source_name = source.get('Source Name', '')
        source_slug = source.get('Slug', '')
        cell = ws.cell(row_idx, 1, source_name)

        if workspace_slug and source_slug:
            source_url = f'https://app.segment.com/{workspace_slug}/sources/{source_slug}/schema'
            cell.hyperlink = source_url
            cell.font = Font(color=colors.BLUE, underline='single')

        # Type
        ws.cell(row_idx, 2, source.get('Type', ''))

        # Connection (Enabled/Disabled)
        enabled = source.get('Enabled', '').lower() == 'true'
        ws.cell(row_idx, 3, 'Enabled' if enabled else 'Disabled')

        # DEV / PROD (left blank as requested)
        ws.cell(row_idx, 4, '')

        # Destinations Receiving
        destinations = source.get('Connected Destinations', '')
        ws.cell(row_idx, 5, destinations)

        # Event Descriptions (left blank - no event data available)
        ws.cell(row_idx, 6, '')

        # Use Case Notes (left blank)
        ws.cell(row_idx, 7, '')

    # Auto-size columns
    column_widths = {
        1: 40,  # Event Source Name (with link)
        2: 20,  # Type
        3: 12,  # Connection
        4: 12,  # DEV / PROD
        5: 60,  # Destinations Receiving
        6: 50,  # Event Descriptions
        7: 30   # Use Case Notes
    }

    for col, width in column_widths.items():
        ws.column_dimensions[ws.cell(1, col).column_letter].width = width

    # Set row height for header
    ws.row_dimensions[1].height = 30

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{customer_name}_Workspace_Analysis.xlsx'
    )

@app.route('/api/event-volumes')
def event_volumes():
    """Get event volumes for workspace"""
    from datetime import datetime, timedelta

    # Get API token and workspace config from session or require re-entry
    api_token = session.get('api_token')
    workspace_id = session.get('workspace_id')
    skip_ssl = session.get('skip_ssl', False)

    if not api_token:
        return jsonify({'error': 'API token not found. Please run audit first.'}), 400

    try:
        auditor = SegmentAuditor(api_token, workspace_id=workspace_id, skip_ssl_verify=skip_ssl)

        # Calculate time ranges
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        # Format as ISO 8601
        end_time = now.isoformat() + 'Z'
        seven_day_start = seven_days_ago.isoformat() + 'Z'
        fourteen_day_start = fourteen_days_ago.isoformat() + 'Z'

        # Get total workspace volumes (no groupBy, just workspace totals)
        seven_day_volume = auditor.get_event_volumes(seven_day_start, end_time, granularity='DAY')
        fourteen_day_volume = auditor.get_event_volumes(fourteen_day_start, end_time, granularity='DAY')

        # Get 7-day volume grouped by sourceId for the chart
        seven_day_by_source = auditor.get_event_volumes(seven_day_start, end_time, granularity='DAY', group_by=['sourceId'])

        return jsonify({
            'seven_day': seven_day_volume,
            'fourteen_day': fourteen_day_volume,
            'seven_day_by_source': seven_day_by_source
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audit_data/<path:filename>')
def serve_data(filename):
    """Serve audit data files"""
    file_path = DATA_DIR / filename
    if file_path.exists():
        from flask import send_file
        return send_file(file_path)
    return f"File not found: {filename}", 404

@app.route('/api/summary')
def api_summary():
    """API endpoint for summary data"""
    summary_file = DATA_DIR / 'audit_summary.json'
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({"error": "Summary file not found"}), 404

@app.route('/reset')
def reset():
    """Reset audit status"""
    global audit_status
    audit_status = {
        'running': False,
        'progress': 0,
        'message': 'Ready',
        'complete': False,
        'error': None
    }
    return redirect(url_for('index'))

@app.route('/upload-schemas', methods=['POST'])
def upload_schemas():
    """Handle CSV upload for tracking plan generator"""
    import uuid
    try:
        project_name = request.form.get('project_name', 'Project').strip()
        files = request.files.getlist('schema_files')

        if not files or len(files) == 0:
            return jsonify({'error': 'No files uploaded'}), 400

        # Create unique upload session ID
        upload_id = str(uuid.uuid4())
        upload_path = UPLOAD_DIR / upload_id
        upload_path.mkdir(exist_ok=True)

        # Save uploaded files to disk
        saved_files = []
        for file in files:
            if file.filename == '':
                continue

            if not file.filename.endswith('.csv'):
                return jsonify({'error': f'Invalid file type: {file.filename}. Only CSV files are allowed.'}), 400

            # Save file to disk
            file_path = upload_path / file.filename
            file.save(file_path)

            saved_files.append(file.filename)

        if len(saved_files) == 0:
            return jsonify({'error': 'No valid CSV files found'}), 400

        # Store only metadata in session
        session['project_name'] = project_name
        session['upload_id'] = upload_id
        session['schema_filenames'] = saved_files

        return jsonify({'success': True, 'redirect': '/tracking-plan-results'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_tracking_plan(schemas_data):
    """Analyze uploaded schemas and generate tracking plan recommendations"""
    import csv
    from io import StringIO
    from collections import defaultdict, Counter

    # Thresholds
    MIN_EVENT_VOLUME = 1000
    LOW_PROPERTY_VOLUME_THRESHOLD = 0.1  # 10% of event volume

    events_data = defaultdict(lambda: {
        'event_volume': 0,
        'properties': {},
        'last_seen': None,
        'sources': []  # Track which files this event appears in
    })

    # Track cross-file analysis
    event_sources = defaultdict(set)  # event_name -> set of source filenames
    property_events = defaultdict(set)  # property_name -> set of event names it appears in

    # Parse all uploaded CSVs
    for schema in schemas_data:
        source_name = schema['filename']
        content = schema['content']
        reader = csv.DictReader(StringIO(content))

        for row in reader:
            event_name = row.get('Event Name', '').strip()
            property_name = row.get('Property Name', '').strip()
            total_volume = int(row.get('Total', 0))
            last_seen = row.get('Last Seen At (UTC)', '')
            planned = row.get('Planned', 'unplanned')

            if not event_name:
                continue

            # Track which source this event appears in
            event_sources[event_name].add(source_name)

            # Track event-level data
            if property_name == ' ' or property_name == '':
                # This is the event itself
                events_data[event_name]['event_volume'] = total_volume
                events_data[event_name]['last_seen'] = last_seen
                if source_name not in events_data[event_name]['sources']:
                    events_data[event_name]['sources'].append(source_name)
            else:
                # This is a property
                events_data[event_name]['properties'][property_name] = {
                    'volume': total_volume,
                    'planned': planned
                }
                # Track property across events
                property_events[property_name].add(event_name)

    # Generate recommendations
    results = []
    discard_count = 0

    for event_name, data in sorted(events_data.items(), key=lambda x: x[1]['event_volume'], reverse=True):
        event_volume = data['event_volume']
        properties = data['properties']
        property_count = len(properties)

        # Determine recommendation
        if event_volume == 0:
            # Track zero volume events but don't include in results
            discard_count += 1
            continue
        elif event_volume < MIN_EVENT_VOLUME:
            recommendation = 'Review'
            flag = '🟡 Low Volume'
            notes = f'Event volume below minimum threshold ({MIN_EVENT_VOLUME:,})'
        else:
            # Check property volumes
            low_volume_props = []
            zero_volume_props = []

            for prop_name, prop_data in properties.items():
                prop_volume = prop_data['volume']
                if prop_volume == 0:
                    zero_volume_props.append(prop_name)
                elif event_volume > 0 and (prop_volume / event_volume) < LOW_PROPERTY_VOLUME_THRESHOLD:
                    low_volume_props.append(prop_name)

            if len(zero_volume_props) > 0 or len(low_volume_props) > 0:
                recommendation = 'Review'
                flag = '🟡 Property Issues'
                notes = f'{len(zero_volume_props)} properties with zero volume, {len(low_volume_props)} with low volume (<10% of event)'
            else:
                recommendation = 'Include'
                flag = '✅ Good'
                notes = 'Event and properties have healthy volume'

        results.append({
            'event_name': event_name,
            'event_volume': event_volume,
            'property_count': property_count,
            'recommendation': recommendation,
            'flag': flag,
            'notes': notes,
            'last_seen': data['last_seen'],
            'properties': properties,
            'sources': data['sources']
        })

    # Generate crossover analysis
    crossover_analysis = {
        'shared_events': [],
        'shared_properties': []
    }

    # Shared events (appear in multiple files)
    if len(schemas_data) > 1:
        for event_name, sources in event_sources.items():
            if len(sources) > 1:
                event_data = events_data[event_name]
                crossover_analysis['shared_events'].append({
                    'event_name': event_name,
                    'source_count': len(sources),
                    'sources': sorted(list(sources)),
                    'event_volume': event_data['event_volume'],
                    'property_count': len(event_data['properties'])
                })

        # Sort by source count (most shared first)
        crossover_analysis['shared_events'].sort(key=lambda x: x['source_count'], reverse=True)

        # Shared properties (appear in multiple events)
        for property_name, events in property_events.items():
            if len(events) > 1 and property_name.strip():  # Ignore empty property names
                crossover_analysis['shared_properties'].append({
                    'property_name': property_name,
                    'event_count': len(events),
                    'events': sorted(list(events))[:10]  # Show up to 10 events
                })

        # Sort by event count (most shared first)
        crossover_analysis['shared_properties'].sort(key=lambda x: x['event_count'], reverse=True)

    return results, crossover_analysis, discard_count

@app.route('/export-tracking-plan-excel')
def export_tracking_plan_excel():
    """Export tracking plan as Excel with multiple sheets"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO

    project_name = session.get('project_name', 'Project')
    upload_id = session.get('upload_id')
    schema_filenames = session.get('schema_filenames', [])

    if not upload_id or not schema_filenames:
        return "No data to export", 404

    upload_path = UPLOAD_DIR / upload_id

    # Load files from disk
    uploaded_schemas = []
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']

    for filename in schema_filenames:
        file_path = upload_path / filename
        if not file_path.exists():
            continue

        content = None
        with open(file_path, 'rb') as f:
            raw_content = f.read()

        for encoding in encodings:
            try:
                content = raw_content.decode(encoding)
                break
            except (UnicodeDecodeError, AttributeError):
                continue

        if content:
            uploaded_schemas.append({'filename': filename, 'content': content})

    if not uploaded_schemas:
        return "No data to export", 404

    # Analyze schemas
    tracking_plan, crossover_analysis, zero_volume_count = analyze_tracking_plan(uploaded_schemas)

    # Create Excel workbook
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Create Summary sheet
    ws_summary = wb.create_sheet("Summary")

    # Header styling
    header_fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    # Summary headers
    headers = ['Flag', 'Event Name', 'Event Volume', 'Properties', 'Recommendation', 'Notes']
    for col, header in enumerate(headers, 1):
        cell = ws_summary.cell(1, col, header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Summary data
    for row_idx, event in enumerate(tracking_plan, 2):
        ws_summary.cell(row_idx, 1, event['flag'])
        ws_summary.cell(row_idx, 2, event['event_name'])
        ws_summary.cell(row_idx, 3, event['event_volume'])
        ws_summary.cell(row_idx, 4, event['property_count'])
        ws_summary.cell(row_idx, 5, event['recommendation'])
        ws_summary.cell(row_idx, 6, event['notes'])

    # Auto-size columns
    for col in ws_summary.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws_summary.column_dimensions[column].width = adjusted_width

    # Create individual event sheets with property details
    for event in tracking_plan[:50]:  # Limit to 50 sheets (Excel limit is 255 but be reasonable)
        # Sanitize sheet name (Excel has 31 char limit and doesn't allow certain chars)
        sheet_name = event['event_name'][:31]
        sheet_name = sheet_name.replace('/', '-').replace('\\', '-').replace('*', '').replace('?', '').replace(':', '-').replace('[', '').replace(']', '')

        try:
            ws_event = wb.create_sheet(sheet_name)
        except:
            continue  # Skip if sheet name is invalid

        # Event details
        ws_event.cell(1, 1, "Event Name").font = Font(bold=True)
        ws_event.cell(1, 2, event['event_name'])
        ws_event.cell(2, 1, "Event Volume").font = Font(bold=True)
        ws_event.cell(2, 2, event['event_volume'])
        ws_event.cell(3, 1, "Recommendation").font = Font(bold=True)
        ws_event.cell(3, 2, event['recommendation'])

        # Properties table
        ws_event.cell(5, 1, "Property Name").font = header_font
        ws_event.cell(5, 1).fill = header_fill
        ws_event.cell(5, 2, "Volume").font = header_font
        ws_event.cell(5, 2).fill = header_fill
        ws_event.cell(5, 3, "Planned").font = header_font
        ws_event.cell(5, 3).fill = header_fill

        # Property data
        properties = event.get('properties', {})
        for prop_idx, (prop_name, prop_data) in enumerate(properties.items(), 6):
            ws_event.cell(prop_idx, 1, prop_name)
            ws_event.cell(prop_idx, 2, prop_data['volume'])
            ws_event.cell(prop_idx, 3, prop_data['planned'])

        # Auto-size columns
        for col in ws_event.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws_event.column_dimensions[column].width = adjusted_width

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{project_name}_tracking_plan.xlsx'
    )

@app.route('/export-segment-tracking-plan-csv')
def export_segment_tracking_plan_csv():
    """Export tracking plan as Segment-compatible CSV for direct import"""
    import csv
    from io import StringIO

    project_name = session.get('project_name', 'Project')
    upload_id = session.get('upload_id')
    schema_filenames = session.get('schema_filenames', [])

    if not upload_id or not schema_filenames:
        return "No data to export", 404

    upload_path = UPLOAD_DIR / upload_id

    # Load files from disk
    uploaded_schemas = []
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']

    for filename in schema_filenames:
        file_path = upload_path / filename
        if not file_path.exists():
            continue

        content = None
        with open(file_path, 'rb') as f:
            raw_content = f.read()

        for encoding in encodings:
            try:
                content = raw_content.decode(encoding)
                break
            except (UnicodeDecodeError, AttributeError):
                continue

        if content:
            uploaded_schemas.append({'filename': filename, 'content': content})

    if not uploaded_schemas:
        return "No data to export", 404

    # Analyze schemas
    tracking_plan, crossover_analysis, zero_volume_count = analyze_tracking_plan(uploaded_schemas)

    # Generate Segment tracking plan CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Version',
        'Event Type',
        'Event Name',
        'Property Name',
        'Source',
        'Description',
        'Labels',
        'Property Status',
        'Property Data Type',
        'Allowed Property Values',
        'Enum Values'
    ])

    # Include all events that meet volume threshold (≥1,000)
    MIN_EVENT_VOLUME = 1000
    significant_events = [e for e in tracking_plan if e['event_volume'] >= MIN_EVENT_VOLUME]

    for event in significant_events:
        event_name = event['event_name']
        properties = event.get('properties', {})
        event_volume = event['event_volume']

        # Event row (no property name)
        writer.writerow([
            '1',                        # Version
            'Track',                    # Event Type
            event_name,                 # Event Name
            '',                         # Property Name (empty for event row)
            'Schema Import',            # Source
            '',                         # Description
            '',                         # Labels
            '',                         # Property Status
            '',                         # Property Data Type
            '',                         # Allowed Property Values
            ''                          # Enum Values
        ])

        # Filter to only healthy properties (no zero volume, no low volume issues)
        healthy_properties = []

        for prop_name, prop_data in properties.items():
            prop_volume = prop_data['volume']

            # Include if property has volume and is at least 10% of event volume
            if prop_volume > 0 and (prop_volume / event_volume) >= 0.1:
                healthy_properties.append((prop_name, prop_data))

        # Property rows
        for prop_name, prop_data in healthy_properties:
            # Determine property status based on planned field
            prop_status = '' if prop_data['planned'] == 'unplanned' else ''

            writer.writerow([
                '1',                    # Version
                'Track',                # Event Type
                event_name,             # Event Name
                prop_name,              # Property Name
                'Schema Import',        # Source
                '',                     # Description
                '',                     # Labels
                prop_status,            # Property Status
                'string',               # Property Data Type (default to string)
                '',                     # Allowed Property Values
                ''                      # Enum Values
            ])

    # Return as downloadable CSV
    from flask import Response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={project_name}_segment_import.csv'
        }
    )

@app.route('/export-crossover-analysis')
def export_crossover_analysis():
    """Export cross-source analysis (shared events and properties) to Excel"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO

    project_name = session.get('project_name', 'Project')
    upload_id = session.get('upload_id')
    schema_filenames = session.get('schema_filenames', [])

    if not upload_id or not schema_filenames:
        return "No data to export", 404

    upload_path = UPLOAD_DIR / upload_id

    # Load files from disk
    uploaded_schemas = []
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']

    for filename in schema_filenames:
        file_path = upload_path / filename
        if not file_path.exists():
            continue

        content = None
        with open(file_path, 'rb') as f:
            raw_content = f.read()

        for encoding in encodings:
            try:
                content = raw_content.decode(encoding)
                break
            except (UnicodeDecodeError, AttributeError):
                continue

        if content:
            uploaded_schemas.append({'filename': filename, 'content': content})

    if not uploaded_schemas:
        return "No data to export", 404

    # Analyze schemas
    tracking_plan, crossover_analysis, zero_volume_count = analyze_tracking_plan(uploaded_schemas)

    # Create Excel workbook
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Header styling
    header_fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    # Sheet 1: Shared Events
    ws_events = wb.create_sheet("Shared Events")

    # Headers
    event_headers = ['Event Name', 'Source Count', 'Source Files', 'Event Volume', 'Property Count']
    for col, header in enumerate(event_headers, 1):
        cell = ws_events.cell(1, col, header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Data
    for row_idx, event in enumerate(crossover_analysis['shared_events'], 2):
        ws_events.cell(row_idx, 1, event['event_name'])
        ws_events.cell(row_idx, 2, event['source_count'])
        ws_events.cell(row_idx, 3, ', '.join(event['sources']))
        ws_events.cell(row_idx, 4, event['event_volume'])
        ws_events.cell(row_idx, 5, event['property_count'])

    # Auto-size columns
    for col in ws_events.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 60)
        ws_events.column_dimensions[column].width = adjusted_width

    # Sheet 2: Shared Properties
    ws_props = wb.create_sheet("Shared Properties")

    # Headers
    prop_headers = ['Property Name', 'Event Count', 'Events Using This Property']
    for col, header in enumerate(prop_headers, 1):
        cell = ws_props.cell(1, col, header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Data
    for row_idx, prop in enumerate(crossover_analysis['shared_properties'], 2):
        ws_props.cell(row_idx, 1, prop['property_name'])
        ws_props.cell(row_idx, 2, prop['event_count'])
        # Join all events (not just the first 10 shown in UI)
        ws_props.cell(row_idx, 3, ', '.join(prop['events']))

    # Auto-size columns
    for col in ws_props.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 60)
        ws_props.column_dimensions[column].width = adjusted_width

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{project_name}_crossover_analysis.xlsx'
    )

@app.route('/tracking-plan-results')
def tracking_plan_results():
    """Display tracking plan generator results"""
    project_name = session.get('project_name', 'Project')
    upload_id = session.get('upload_id')
    schema_filenames = session.get('schema_filenames', [])

    if not upload_id or not schema_filenames:
        return redirect(url_for('index'))

    upload_path = UPLOAD_DIR / upload_id

    # Load files from disk with encoding detection
    uploaded_schemas = []
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']

    for filename in schema_filenames:
        file_path = upload_path / filename
        if not file_path.exists():
            continue

        # Try different encodings
        content = None
        with open(file_path, 'rb') as f:
            raw_content = f.read()

        for encoding in encodings:
            try:
                content = raw_content.decode(encoding)
                break
            except (UnicodeDecodeError, AttributeError):
                continue

        if content:
            uploaded_schemas.append({
                'filename': filename,
                'content': content
            })

    if not uploaded_schemas:
        return redirect(url_for('index'))

    # Analyze schemas
    tracking_plan, crossover_analysis, zero_volume_count = analyze_tracking_plan(uploaded_schemas)

    # Calculate stats (zero volume events are already filtered out)
    total_events = len(tracking_plan)
    include_count = len([e for e in tracking_plan if e['recommendation'] == 'Include'])
    review_count = len([e for e in tracking_plan if e['recommendation'] == 'Review'])

    return render_template('tracking_plan_results.html',
                         project_name=project_name,
                         schemas=uploaded_schemas,
                         tracking_plan=tracking_plan,
                         crossover_analysis=crossover_analysis,
                         stats={
                             'total': total_events,
                             'include': include_count,
                             'review': review_count,
                             'discard': zero_volume_count
                         })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print("=" * 80)
    print("Segment Audit Dashboard")
    print("=" * 80)
    print("\n🚀 Starting server...")
    print(f"📁 Data directory: {DATA_DIR.absolute()}")
    print(f"\n📊 Dashboard URL: http://localhost:{port}")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 80 + "\n")

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
