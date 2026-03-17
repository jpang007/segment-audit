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

    def get_audiences(self):
        """Get all audiences"""
        if not self.space_id:
            return []
        url = f"{self.v1_base}/spaces/{self.space_id}/audiences"
        return self._paginate(url, 'data')

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

def run_audit(api_token, workspace_id, space_ids, customer_name, skip_ssl_verify=False):
    """Run the audit in background thread"""
    global audit_status

    try:
        audit_status = {
            'running': True,
            'progress': 10,
            'message': 'Connecting to Segment API...',
            'complete': False,
            'error': None
        }

        # Parse space IDs (comma separated)
        space_list = [s.strip() for s in space_ids.split(',') if s.strip()]

        all_audiences = []
        all_events = Counter()
        all_traits = Counter()
        sources_data = []

        # Collect sources (always - API token is workspace-scoped)
        audit_status['message'] = 'Collecting source data...'
        audit_status['progress'] = 20

        auditor = SegmentAuditor(api_token, workspace_id=workspace_id, skip_ssl_verify=skip_ssl_verify)
        sources = auditor.get_sources()

        for source in sources:
            metadata = source.get('metadata', {})
            source_type = metadata.get('name', 'Unknown')

            # Skip Personas sources (Segment-generated)
            if source_type == 'Personas':
                continue

            categories = metadata.get('categories', [])
            write_keys = source.get('writeKeys', [])
            labels = source.get('labels', [])

            # Ensure all items are strings
            categories_str = ', '.join(str(c) for c in categories) if categories else 'Unknown'
            write_keys_str = ', '.join(str(w) for w in write_keys) if write_keys else ''
            # Labels might be dicts with 'key' field, or strings
            labels_str = ', '.join(
                label.get('key', str(label)) if isinstance(label, dict) else str(label)
                for label in labels
            ) if labels else ''

            sources_data.append({
                'Source ID': source.get('id'),
                'Source Name': source.get('name'),
                'Slug': source.get('slug'),
                'Enabled': source.get('enabled', False),
                'Type': source_type,
                'Category': categories_str,
                'Write Keys': write_keys_str,
                'Labels': labels_str
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
        summary = {
            'audit_date': datetime.now().isoformat(),
            'customer_name': customer_name,
            'workspace_id': workspace_id,
            'space_ids': space_list,
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
    workspace_id = request.form.get('workspace_id', '').strip()
    space_ids = request.form.get('space_ids', '').strip()
    customer_name = request.form.get('customer_name', 'Customer').strip()
    skip_ssl = request.form.get('skip_ssl') == 'true'  # Checkbox returns 'true' or None

    # Validate
    if not api_token:
        return jsonify({'error': 'API token is required'}), 400
    if not space_ids:
        return jsonify({'error': 'At least one space ID is required'}), 400

    # Store customer name in session
    session['customer_name'] = customer_name

    # Reset status
    audit_status = {
        'running': True,
        'progress': 0,
        'message': 'Starting audit...',
        'complete': False,
        'error': None
    }

    # Run audit in background thread
    thread = threading.Thread(
        target=run_audit,
        args=(api_token, workspace_id, space_ids, customer_name, skip_ssl)
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
    return jsonify(audit_status)

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
