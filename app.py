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

    # Store credentials in session for later use
    session['customer_name'] = customer_name
    session['api_token'] = api_token
    session['workspace_id'] = workspace_id
    session['skip_ssl'] = skip_ssl

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

@app.route('/observability')
def observability():
    """Observability view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('observability.html', customer_name=customer_name)

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
