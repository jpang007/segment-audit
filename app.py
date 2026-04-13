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
from datetime import datetime, timedelta
import requests
from collections import Counter

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Session configuration - keep sessions alive for 7 days
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

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

    def __init__(self, api_token, workspace_id=None, space_id=None, skip_ssl_verify=False, gateway_token=None, workspace_slug=None):
        self.api_token = api_token
        self.gateway_token = gateway_token
        self.workspace_id = workspace_id
        self.workspace_slug = workspace_slug
        self.space_id = space_id
        self.skip_ssl_verify = skip_ssl_verify
        self.verify = not skip_ssl_verify  # If skip_ssl_verify=True, verify=False
        self.v1_base = "https://api.segmentapis.com"
        self.platform_base = "https://platform.segmentapis.com/v1beta"
        self.gateway_api_base = "https://app.segment.com/gateway-api"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        # Gateway API headers (if token provided)
        if gateway_token:
            self.gateway_headers = {
                "Authorization": f"Bearer {gateway_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-requested-with": "fetch"
            }
        else:
            self.gateway_headers = None

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

        try:
            response = requests.get(url, headers=self.headers, timeout=30, verify=self.verify)

            if response.status_code != 200:
                return []

            data = response.json()

            # API returns destinations in data.destinations
            destinations_wrapper = data.get('data', {})

            if isinstance(destinations_wrapper, dict):
                destinations = destinations_wrapper.get('destinations', [])
                return destinations
            return []
        except Exception as e:
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

    # COMMENTED OUT: Audience destinations API is in Alpha and not production-ready
    # TODO: Re-enable when Segment releases this endpoint to general availability or implement via GraphQL
    # def get_audience_destinations(self, audience_id):
    #     """Get all destinations connected to an audience
    #
    #     Note: This endpoint is in Alpha and may not be available for all workspaces.
    #     Requires the Audience feature to be enabled in the workspace.
    #     Rate limit: 50 requests per minute.
    #     """
    #     if not self.space_id:
    #         return []
    #     url = f"{self.v1_base}/spaces/{self.space_id}/audiences/{audience_id}/destinations"
    #
    #     try:
    #         response = requests.get(url, headers=self.headers, timeout=30, verify=self.verify)
    #
    #         if response.status_code == 403:
    #             # Alpha endpoint not available or workspace lacks Audience feature
    #             print(f"⚠️ Cannot access audience destinations (Alpha API): 403 Forbidden. This workspace may not have the Audience feature enabled or API token lacks permissions.")
    #             return None  # Return None to signal this is a permission issue, not just empty
    #         elif response.status_code == 404:
    #             # Audience not found or endpoint not available
    #             return []
    #         elif response.status_code == 429:
    #             # Rate limited (50 requests per minute for this Alpha endpoint)
    #             print(f"⚠️ Rate limited on audience destinations API (50/min limit)")
    #             return []
    #         elif response.status_code != 200:
    #             print(f"⚠️ Audience destinations API returned {response.status_code}: {response.text[:200]}")
    #             return []
    #
    #         data = response.json()
    #
    #         # API returns destinations in data.destinations
    #         destinations_wrapper = data.get('data', {})
    #
    #         if isinstance(destinations_wrapper, dict):
    #             destinations = destinations_wrapper.get('destinations', [])
    #             return destinations
    #         elif isinstance(destinations_wrapper, list):
    #             return destinations_wrapper
    #         return []
    #     except Exception as e:
    #         print(f"Warning: Could not fetch destinations for audience {audience_id}: {e}")
    #         return []

    def get_audiences_gateway(self, workspace_slug, space_id):
        """Fetch audiences with destinations via Gateway API (GraphQL)

        Returns a dict mapping audience_id to enhanced data:
        {
            'audience_id_123': {
                'destinations': ['Destination 1', 'Destination 2'],
                'destination_count': 2,
                'definition_type': 'ast',
                'definition_options': {...},
                'collection': 'USERS',
                'status': 'SUCCEEDED'
            }
        }
        """
        if not self.gateway_headers:
            print("⚠️ Gateway API token not provided, skipping audience destinations fetch")
            return {}

        url = f"{self.gateway_api_base}/graphql"

        # GraphQL query to fetch audiences with destinations
        query = """
        query GetAudiences($workspaceSlug: Slug!, $spaceId: String!, $cursor: RecordCursorInput!) {
          workspace(slug: $workspaceSlug) {
            id
            space(id: $spaceId) {
              id
              name
              slug
              audiencesAndFolders(cursor: $cursor) {
                cursor {
                  hasMore
                  next
                }
                data {
                  __typename
                  ... on RealtimeAudience {
                    id
                    name
                    key
                    enabled
                    collection
                    status
                    size
                    definition {
                      type
                      options
                    }
                    destinations {
                      id
                      name
                      enabled
                    }
                  }
                  ... on RetlAudience {
                    id
                    name
                    key
                    enabled
                    collection
                    status
                    size
                    destinations {
                      id
                      name
                      enabled
                    }
                  }
                }
              }
            }
          }
        }
        """

        variables = {
            "workspaceSlug": workspace_slug,
            "spaceId": space_id,
            "cursor": {
                "limit": 1000
            }
        }

        payload = {
            "query": query,
            "variables": variables
        }

        try:
            response = requests.post(url, headers=self.gateway_headers, json=payload, timeout=30, verify=self.verify)

            if response.status_code == 401:
                print("⚠️ Gateway API authentication failed (401). Token may be expired. Continuing without audience destinations.")
                return {}
            elif response.status_code != 200:
                print(f"⚠️ Gateway API returned {response.status_code}. Continuing without audience destinations.")
                return {}

            data = response.json()

            # Check for GraphQL errors
            if 'errors' in data:
                print(f"⚠️ Gateway API GraphQL errors:")
                for error in data['errors']:
                    print(f"   - {error.get('message', error)}")
                return {}

            # Parse response
            workspace_data = data.get('data', {}).get('workspace')
            if not workspace_data:
                print("⚠️ No workspace data in Gateway API response")
                return {}

            space_data = workspace_data.get('space')
            if not space_data:
                print("⚠️ No space data in Gateway API response")
                return {}

            audiences_and_folders = space_data.get('audiencesAndFolders', {})
            data_items = audiences_and_folders.get('data', [])

            # Build mapping of audience_id to enhanced data
            audience_map = {}
            for item in data_items:
                typename = item.get('__typename', '')

                # Skip folders
                if typename == 'Folder':
                    continue

                audience_id = item.get('id')
                if not audience_id:
                    continue

                # Extract destinations
                destinations = item.get('destinations', []) or []
                destination_names = [d.get('name', '') for d in destinations if d.get('name')]

                # Extract definition
                definition = item.get('definition', {}) or {}
                definition_type = definition.get('type', '')
                definition_options = definition.get('options', {})

                audience_map[audience_id] = {
                    'destinations': destination_names,
                    'destination_count': len(destination_names),
                    'definition_type': definition_type,
                    'definition_options': str(definition_options) if definition_options else '',
                    'collection': item.get('collection', ''),
                    'status': item.get('status', '')
                }

            print(f"✅ Gateway API: Fetched enhanced data for {len(audience_map)} audiences")
            return audience_map

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Gateway API request failed: {e}. Continuing without audience destinations.")
            return {}
        except Exception as e:
            print(f"⚠️ Gateway API error: {e}. Continuing without audience destinations.")
            return {}

    def get_computed_traits(self):
        """Get all computed traits"""
        if not self.space_id:
            return []
        url = f"{self.v1_base}/spaces/{self.space_id}/computed-traits"
        return self._paginate(url, 'data')

    def get_reverse_etl_models(self):
        """Get all Reverse ETL models"""
        url = f"{self.v1_base}/reverse-etl-models"
        return self._paginate(url, 'data')

    def get_warehouses(self):
        """Get all data warehouse connections"""
        url = f"{self.v1_base}/warehouses"
        return self._paginate(url, 'data')

    def get_warehouse_connection_state(self, warehouse_id):
        """Get connection state for a specific warehouse"""
        url = f"{self.v1_base}/warehouses/{warehouse_id}/connection-state"
        try:
            response = requests.get(url, headers=self.headers, verify=self.verify, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Warning: Could not fetch connection state for warehouse {warehouse_id}: {e}")
            return None

    def get_warehouse_sync_reports(self, warehouse_id, limit=500):
        """Get sync reports for a warehouse"""
        url = f"{self.v1_base}/warehouses/{warehouse_id}/syncs"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=self.verify,
                timeout=30,
                params={'pagination.count': limit}
            )
            if response.status_code == 200:
                data = response.json()
                reports = data.get('data', {}).get('reports', [])
                return reports
            return []
        except Exception as e:
            print(f"Warning: Could not fetch sync reports for warehouse {warehouse_id}: {e}")
            return []

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

    def _graphql_query(self, query, variables=None):
        """Execute a GraphQL query against Segment's API"""
        url = f"{self.platform_base}/graphql"

        payload = {
            'query': query
        }

        if variables:
            payload['variables'] = variables

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30,
                    verify=self.verify
                )

                if response.status_code != 200:
                    raise Exception(f"GraphQL API Error: {response.status_code} - {response.text}")

                data = response.json()

                # Check for GraphQL errors
                if 'errors' in data:
                    errors = data['errors']
                    error_messages = ', '.join([e.get('message', str(e)) for e in errors])
                    raise Exception(f"GraphQL Error: {error_messages}")

                return data.get('data', {})

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    ssl_hint = " Try enabling 'Skip SSL Verification' checkbox if you're behind a VPN." if "SSL" in str(e) or "certificate" in str(e).lower() else ""
                    raise Exception(f"Network Error: Unable to connect to Segment GraphQL API after {max_retries} attempts.{ssl_hint} Error: {str(e)}")

    def get_delivery_metrics(self, source_id, destination_id, start_time=None, end_time=None, granularity='HOUR'):
        """Get delivery metrics for a specific source-destination pair using REST API

        Args:
            source_id: The source ID
            destination_id: The destination ID (not metadata ID)
            start_time: ISO format datetime string (defaults to 24 hours ago)
            end_time: ISO format datetime string (defaults to now)
            granularity: MINUTE, HOUR, or DAY (defaults to HOUR for 24hr window)
        """

        # Default to last 24 hours if not specified
        if not start_time or not end_time:
            now = datetime.now()
            end_time = now.isoformat() + 'Z'
            start_time = (now - timedelta(hours=24)).isoformat() + 'Z'

        # REST API endpoint: GET /destinations/{destinationId}/delivery-metrics
        url = f"{self.v1_base}/destinations/{destination_id}/delivery-metrics"

        params = {
            'sourceId': source_id,
            'startTime': start_time,
            'endTime': end_time,
            'granularity': granularity
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30,
                    verify=self.verify
                )

                if response.status_code == 200:
                    data = response.json()
                    # Return the deliveryMetricsSummary which contains sourceId, destinationId, and metrics array
                    return data.get('data', {}).get('deliveryMetricsSummary', {})
                elif response.status_code == 404:
                    # Destination not found or no metrics available
                    return None
                elif response.status_code == 403:
                    raise Exception(f"API Error: 403 - Not authorized to access delivery metrics")
                else:
                    raise Exception(f"API Error: {response.status_code} - {response.text}")

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    ssl_hint = " Try enabling 'Skip SSL Verification' checkbox if you're behind a VPN." if "SSL" in str(e) or "certificate" in str(e).lower() else ""
                    raise Exception(f"Network Error: Unable to connect to Segment API after {max_retries} attempts.{ssl_hint} Error: {str(e)}")

        return None

def infer_computed_trait_type(definition):
    """Infer the type of computed trait from its definition"""
    if not isinstance(definition, dict):
        return 'Unknown'

    query = definition.get('query', '').lower()

    # Check for aggregation types
    if '.count()' in query:
        return 'Event Count'
    elif '.sum(' in query:
        return 'Sum Aggregation'
    elif '.avg(' in query or '.average(' in query:
        return 'Average Aggregation'
    elif '.min(' in query:
        return 'Minimum Value'
    elif '.max(' in query:
        return 'Maximum Value'
    elif 'most_frequent' in query or '.most(' in query or '.mode(' in query or 'mode(' in query:
        return 'Most Frequent'
    elif 'least_frequent' in query or '.least(' in query:
        return 'Least Frequent'
    elif 'first(' in query or '.first' in query:
        return 'First Occurrence'
    elif 'last(' in query or '.last' in query:
        return 'Last Occurrence'
    elif '.unique.count()' in query or 'unique_count' in query:
        return 'Unique Count'
    elif '.unique' in query or 'unique()' in query or 'distinct' in query:
        return 'Unique List'
    elif 'trait(' in query and 'event(' not in query:
        return 'Trait Transformation'
    else:
        return 'Custom'

def run_audit(api_token, skip_ssl_verify=False, gateway_token=None):
    """Run the audit in background thread"""
    global audit_status

    try:
        # Log token for debugging
        token_prefix = api_token[:30] if len(api_token) > 30 else api_token[:20]
        token_suffix = api_token[-10:] if len(api_token) > 40 else ""
        print(f"=== AUDIT STARTING WITH TOKEN: {token_prefix}...{token_suffix}", flush=True)
        print(f"=== TOKEN LENGTH: {len(api_token)}", flush=True)

        if gateway_token:
            print(f"=== GATEWAY API TOKEN PROVIDED: {gateway_token[:30]}...{gateway_token[-10:]}", flush=True)
        else:
            print("=== GATEWAY API TOKEN NOT PROVIDED (audience destinations will not be fetched)", flush=True)

        audit_status = {
            'running': True,
            'progress': 3,
            'message': 'Fetching workspace information...',
            'complete': False,
            'error': None
        }

        # Clear old data files to ensure fresh start
        old_files = [
            'segment_audiences_audit.csv',
            'segment_computed_traits_audit.csv',
            'segment_sources_audit.csv',
            'segment_retl_models.json',
            'segment_warehouses.json',
            'event_coverage.csv',
            'trait_coverage.csv',
            'segment_event_volumes.json'
        ]
        for filename in old_files:
            file_path = DATA_DIR / filename
            if file_path.exists():
                file_path.unlink()

        # Fetch workspace info from token
        auditor = SegmentAuditor(api_token, skip_ssl_verify=skip_ssl_verify, gateway_token=gateway_token)
        workspace = auditor.get_workspace()

        workspace_id = workspace.get('id')
        workspace_slug = workspace.get('slug', workspace.get('name'))
        workspace_name = workspace.get('display_name', workspace.get('name', workspace_slug))

        # Update auditor with workspace_slug for Gateway API calls
        auditor.workspace_slug = workspace_slug

        audit_status['progress'] = 5
        audit_status['message'] = f'Found workspace: {workspace_name}. Fetching spaces...'

        # Fetch all spaces automatically
        spaces = auditor.get_spaces()
        space_list = [space.get('id') for space in spaces if space.get('id')]
        print(f"=== FETCHED {len(spaces)} SPACES FROM API", flush=True)
        print(f"=== SPACE IDS: {space_list}", flush=True)

        # Create space mapping (ID -> Name) for better readability
        space_mapping = {space.get('id'): space.get('name', space.get('id')) for space in spaces if space.get('id')}

        # Create space slug mapping (ID -> Slug) for URLs
        space_slug_mapping = {space.get('id'): space.get('slug', space.get('name', space.get('id'))) for space in spaces if space.get('id')}

        if not space_list:
            raise Exception("No spaces found in workspace. Make sure your workspace has the Spaces feature enabled.")

        audit_status['progress'] = 10
        audit_status['message'] = f'Found {len(space_list)} space(s). Connecting to Segment API...'

        all_audiences = []
        all_computed_traits = []
        computed_traits_access_error = None
        all_events = Counter()
        all_traits = Counter()
        sources_data = []
        retl_models_data = []
        warehouses_data = []

        # Collect sources (always - API token is workspace-scoped)
        audit_status['message'] = 'Collecting source data...'
        audit_status['progress'] = 20

        # Re-use the existing auditor that already has gateway_token
        # auditor = SegmentAuditor(api_token, workspace_id=workspace_id, skip_ssl_verify=skip_ssl_verify)
        auditor.workspace_id = workspace_id  # Update with workspace_id for sources collection
        sources = auditor.get_sources()

        # Collect Reverse ETL models
        audit_status['message'] = 'Collecting Reverse ETL models...'
        try:
            retl_models = auditor.get_reverse_etl_models()
            for model in retl_models:
                retl_models_data.append({
                    'ID': model.get('id', ''),
                    'Name': model.get('name', ''),
                    'Source ID': model.get('sourceId', ''),
                    'Enabled': model.get('enabled', False),
                    'Query': model.get('query', ''),
                    'Query Identifier Column': model.get('queryIdentifierColumn', '')
                })
        except Exception as e:
            # If RETL models API fails, continue without them
            print(f"Warning: Could not fetch Reverse ETL models: {e}")

        # Collect Warehouses
        audit_status['message'] = 'Collecting warehouse connections...'
        try:
            warehouses = auditor.get_warehouses()
            # Fetch connection state and selective syncs for each warehouse
            for idx, warehouse in enumerate(warehouses):
                warehouse_id = warehouse.get('id')
                if warehouse_id:
                    audit_status['message'] = f'Checking warehouse connection {idx+1}/{len(warehouses)}...'

                    # Get connection state
                    connection_state = auditor.get_warehouse_connection_state(warehouse_id)
                    if connection_state:
                        warehouse['connectionState'] = connection_state

                    # Get selective syncs
                    audit_status['message'] = f'Collecting selective syncs for warehouse {idx+1}/{len(warehouses)}...'
                    try:
                        selective_syncs = auditor.get_warehouse_sync_reports(warehouse_id)
                        warehouse['selectiveSyncs'] = selective_syncs

                        # Count unique sources
                        unique_sources = set(sync.get('sourceId') for sync in selective_syncs if sync.get('sourceId'))
                        print(f"Found {len(selective_syncs)} sync reports across {len(unique_sources)} sources for warehouse {warehouse.get('settings', {}).get('name', warehouse_id)}")
                    except Exception as sync_error:
                        print(f"Warning: Could not fetch selective syncs for warehouse {warehouse_id}: {sync_error}")
                        warehouse['selectiveSyncs'] = []

            warehouses_data = warehouses
        except Exception as e:
            # If warehouses API fails, continue without them
            print(f"Warning: Could not fetch warehouses: {e}")

        # Map Personas sources to spaces by matching slugs
        # Personas slugs follow pattern: personas_{space-slug} or personas_{space-slug}{number}
        # Note: Personas slugs use underscores, space slugs use hyphens
        def match_personas_to_space(personas_slug, space_slug_mapping):
            """Match a Personas source slug to its space"""
            if not personas_slug.startswith('personas_'):
                return None

            import re

            # Remove 'personas_' prefix
            stripped = personas_slug[9:]  # len('personas_') = 9

            # Try exact match first (rare, but possible)
            for space_id, space_slug in space_slug_mapping.items():
                if stripped == space_slug:
                    return space_id

            # Try matching with trailing number removed and underscores replaced with hyphens
            # e.g., personas_jeremy_test2 -> jeremy_test2 -> jeremy_test -> jeremy-test
            stripped_no_number = re.sub(r'\d+$', '', stripped)
            stripped_normalized = stripped_no_number.replace('_', '-')

            for space_id, space_slug in space_slug_mapping.items():
                if stripped_normalized == space_slug:
                    return space_id

            # Also try without removing numbers (e.g., personas_demo-space directly)
            stripped_normalized_with_number = stripped.replace('_', '-')
            for space_id, space_slug in space_slug_mapping.items():
                if stripped_normalized_with_number == space_slug:
                    return space_id

            return None

        for idx, source in enumerate(sources):
            metadata = source.get('metadata', {})
            source_type = metadata.get('name', 'Unknown')

            # Mark Personas/Engage sources (don't skip, just flag them)
            is_engage = source_type == 'Personas'

            # Map Personas source to its space
            personas_space_id = None
            personas_space_name = None
            if is_engage:
                source_slug = source.get('slug', '')
                personas_space_id = match_personas_to_space(source_slug, space_slug_mapping)
                if personas_space_id:
                    personas_space_name = space_mapping.get(personas_space_id, '')

            categories = metadata.get('categories', [])
            # Use first category as the type (e.g., "Website" instead of "Javascript")
            category_type = categories[0] if categories and len(categories) > 0 else source_type
            write_keys = source.get('writeKeys', [])
            labels = source.get('labels', [])

            # Get source logo URL (only if it's a valid URL)
            source_logo = metadata.get('logos', {}).get('default', '')
            if source_logo and not source_logo.startswith('http'):
                source_logo = ''  # Clear non-URL values

            # Get connected destinations for this source
            audit_status['message'] = f'Collecting destinations for source {idx+1}/{len(sources)}...'
            destinations_list = []
            destination_logos = {}
            destination_objects = []  # Keep full destination objects for metrics collection
            try:
                source_id = source.get('id')
                destinations = auditor.get_source_destinations(source_id)

                for dest in destinations:
                    dest_name = dest.get('name', '')
                    dest_metadata = dest.get('metadata', {})
                    dest_slug = dest_metadata.get('slug', '')
                    dest_logo = dest_metadata.get('logos', {}).get('default', '')
                    dest_id = dest.get('id', '')

                    if dest_slug:
                        destinations_list.append(dest_slug)
                        if dest_logo:
                            destination_logos[dest_slug] = dest_logo

                    # Store full destination object for metrics collection
                    if dest_id:
                        destination_objects.append({
                            'id': dest_id,
                            'name': dest_name,
                            'slug': dest_slug,
                            'metadataId': dest_metadata.get('id', '')
                        })
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
                'Destination Count': len(destinations_list),
                'Logo URL': source_logo,
                'Is Engage': is_engage,
                'Space': personas_space_name or '',
                'Space ID': personas_space_id or '',
                '_destination_objects': destination_objects  # Internal field for metrics collection
            })

        # Collect delivery metrics for source-destination pairs (non-engage, non-warehouse sources only)
        # Note: Skip warehouse sources (RETL) since they're harder to visualize without model context
        audit_status['message'] = 'Collecting delivery metrics for connected sources...'
        audit_status['progress'] = 25

        delivery_metrics_data = []

        # Count total source-destination pairs (excluding engage and warehouse sources)
        total_pairs = sum(
            len(src.get('_destination_objects', []))
            for src in sources_data
            if src.get('_destination_objects')
            and not src.get('Is Engage')
            and src.get('Type') != 'Warehouse'  # Skip RETL/warehouse sources
        )

        if total_pairs > 0:
            print(f"=== Collecting delivery metrics for {total_pairs} connection source-destination pairs (excluding RETL/warehouses)...")

            # Get time range for metrics (last 7 days)
            from datetime import timedelta
            now = datetime.now()
            end_time = now.isoformat() + 'Z'
            start_time = (now - timedelta(days=7)).isoformat() + 'Z'

            pair_count = 0
            graphql_access_denied = False

            for src in sources_data:
                # Skip engage sources and warehouse sources (RETL) - only collect metrics for direct connections
                if src.get('Is Engage') or src.get('Type') == 'Warehouse':
                    continue

                source_id = src.get('Source ID')
                source_name = src.get('Source Name', '')
                source_slug = src.get('Slug', '')
                source_type = src.get('Type', '')
                destination_objs = src.get('_destination_objects', [])

                if not destination_objs:
                    continue

                for dest in destination_objs:
                    # If we've already detected API access is denied, skip remaining calls
                    if graphql_access_denied:
                        break

                    pair_count += 1
                    dest_name = dest.get('name', '')
                    dest_id = dest.get('id', '')

                    # Skip if we don't have the destination ID
                    if not dest_id:
                        print(f"Warning: No destination ID for {dest_name}, skipping metrics")
                        continue

                    audit_status['message'] = f'Collecting metrics for {source_name} → {dest_name} ({pair_count}/{total_pairs})...'
                    audit_status['progress'] = 25 + (5 * pair_count // total_pairs)

                    try:
                        metrics = auditor.get_delivery_metrics(
                            source_id=source_id,
                            destination_id=dest_id,
                            start_time=start_time,
                            end_time=end_time,
                            granularity='DAY'  # Daily granularity for 7-day window
                        )

                        if metrics and metrics.get('metrics'):
                            delivery_metrics_data.append({
                                'source_id': source_id,
                                'source_name': source_name,
                                'source_slug': source_slug,
                                'source_type': source_type,
                                'destination_id': dest_id,
                                'destination_name': dest_name,
                                'destination_slug': dest.get('slug', ''),
                                'metrics': metrics.get('metrics', []),  # Extract the metrics array
                                'daily_metrics': metrics.get('deliveryMetrics', []),  # Daily breakdown
                                'collection_time': now.isoformat(),
                                'time_range': {
                                    'start': start_time,
                                    'end': end_time
                                }
                            })
                            print(f"✓ Collected 7-day metrics for {source_name} → {dest_name}")
                        elif metrics:
                            print(f"⚠️ No metrics data returned for {source_name} → {dest_name}")
                    except Exception as e:
                        error_str = str(e)
                        # Check if this is a 403/forbidden error
                        if '403' in error_str or 'forbidden' in error_str.lower() or 'Not authorized' in error_str:
                            print(f"⚠️ API access denied (403). Your API token does not have permission to access delivery metrics.")
                            print(f"   Skipping delivery metrics collection for remaining source-destination pairs.")
                            graphql_access_denied = True
                            break
                        else:
                            print(f"Warning: Could not fetch metrics for {source_name} → {dest_name}: {e}")
                            continue

                # Break outer loop if access was denied
                if graphql_access_denied:
                    break

            if graphql_access_denied:
                print(f"=== Delivery metrics collection skipped due to insufficient API permissions")
            elif len(delivery_metrics_data) > 0:
                print(f"=== Collected 7-day delivery metrics for {len(delivery_metrics_data)} source-destination pairs")
            else:
                print(f"=== No delivery metrics collected")
        else:
            print("=== No connected sources found (excluding Engage/RETL sources), skipping delivery metrics collection")

        # Collect audiences from each space
        # Note: List Spaces API returns all spaces including deleted ones
        # We'll filter out empty spaces (deleted spaces have no audiences)
        total_spaces = len(space_list)
        spaces_with_audiences = []
        print(f"=== DEBUG: Total spaces to process: {total_spaces}, space_list: {space_list}", flush=True)

        # Pre-fetch Gateway API data for all spaces (if token provided)
        gateway_data_by_space = {}
        if gateway_token and workspace_slug:
            audit_status['message'] = f'Fetching audience destinations via Gateway API...'
            print(f"=== Fetching audience destinations via Gateway API for {total_spaces} spaces", flush=True)
            for space_id in space_list:
                try:
                    gateway_audiences = auditor.get_audiences_gateway(workspace_slug, space_id)
                    if gateway_audiences:
                        gateway_data_by_space[space_id] = gateway_audiences
                        print(f"=== Gateway API: Got {len(gateway_audiences)} audiences for space {space_id}", flush=True)
                except Exception as e:
                    print(f"⚠️ Gateway API failed for space {space_id}: {e}", flush=True)

        for idx, space_id in enumerate(space_list):
            audit_status['message'] = f'Collecting audiences from space {idx+1}/{total_spaces}...'
            audit_status['progress'] = 30 + (40 * idx // total_spaces)
            print(f"=== DEBUG: Processing space {idx+1}/{total_spaces}: {space_id}", flush=True)

            auditor = SegmentAuditor(api_token, space_id=space_id, skip_ssl_verify=skip_ssl_verify, gateway_token=gateway_token, workspace_slug=workspace_slug)
            audiences = auditor.get_audiences()

            # Get Gateway API data for this space
            gateway_audiences = gateway_data_by_space.get(space_id, {})

            # Track non-empty spaces
            if len(audiences) > 0:
                spaces_with_audiences.append(space_id)
            else:
                print(f"=== DEBUG: Space {space_id} has no audiences (possibly deleted)", flush=True)

            for aud_idx, audience in enumerate(audiences):
                # Extract size.count from size object
                size_obj = audience.get('size', {})
                size_count = size_obj.get('count', 0) if isinstance(size_obj, dict) else size_obj

                # Get definition and extract query
                definition = audience.get('definition', {})
                definition_query = definition.get('query', '') if isinstance(definition, dict) else ''

                # Get audience ID for Gateway API lookup
                audience_id = audience.get('id', '')

                # Merge Gateway API data (if available)
                gateway_info = gateway_audiences.get(audience_id, {})
                destination_names = gateway_info.get('destinations', [])
                destination_count = gateway_info.get('destination_count', 0)
                definition_type = gateway_info.get('definition_type', '')
                definition_options = gateway_info.get('definition_options', '')
                collection_type = gateway_info.get('collection', '')
                status = gateway_info.get('status', '')

                audience_data = {
                    'ID': audience_id,
                    'Enabled': audience.get('enabled', False),
                    'Name': audience.get('name'),
                    'Key': audience.get('key'),
                    'Size': size_count,
                    'Description': audience.get('description', ''),
                    'Definition Query': definition_query,
                    'Connected Destinations': ', '.join(destination_names) if destination_names else '',
                    'Destination Count': destination_count,
                    'Definition Type': definition_type,
                    'Definition Options': definition_options,
                    'Collection': collection_type,
                    'Status': status,
                    'Created By': audience.get('createdBy', ''),
                    'Created At': audience.get('createdAt', ''),
                    'Updated At': audience.get('updatedAt', ''),
                    'Space ID': space_id
                }
                all_audiences.append(audience_data)

                # Extract events and traits
                events, traits = auditor.extract_events_and_traits(definition)

                for event in events:
                    all_events[event] += 1
                for trait in traits:
                    all_traits[trait] += 1

            # Collect computed traits from this space
            try:
                computed_traits = auditor.get_computed_traits()
                for ct in computed_traits:
                    # Extract the definition to infer type
                    definition = ct.get('definition', {})
                    definition_query = definition.get('query', '') if isinstance(definition, dict) else ''

                    # Infer computed trait type from definition
                    ct_type = infer_computed_trait_type(definition)

                    computed_trait_data = {
                        'ID': ct.get('id', ''),
                        'Enabled': ct.get('enabled', False),
                        'Name': ct.get('name', ''),
                        'Key': ct.get('key', ''),
                        'Type': ct_type,
                        'Definition': definition_query,
                        'Created At': ct.get('createdAt', ''),
                        'Updated At': ct.get('updatedAt', ''),
                        'Space ID': space_id
                    }
                    all_computed_traits.append(computed_trait_data)
            except Exception as e:
                error_str = str(e)
                print(f"Warning: Could not fetch computed traits for space {space_id}: {e}")

                # Check if it's a 403 forbidden error (private beta access needed)
                if '403' in error_str or 'forbidden' in error_str.lower() or 'Not authorized' in error_str:
                    computed_traits_access_error = 'no_access'

        # Save data files
        audit_status['message'] = 'Saving audit data...'
        audit_status['progress'] = 80

        # Filter out empty spaces (deleted spaces have no audiences)
        filtered_space_mapping = {sid: space_mapping[sid] for sid in spaces_with_audiences if sid in space_mapping}
        filtered_space_slug_mapping = {sid: space_slug_mapping[sid] for sid in spaces_with_audiences if sid in space_slug_mapping}

        print(f"=== DEBUG: Filtered spaces from {len(space_list)} to {len(spaces_with_audiences)} active spaces", flush=True)

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
            'space_ids': spaces_with_audiences,  # Only active spaces
            'space_mapping': filtered_space_mapping,  # ID -> Name mapping
            'space_slug_mapping': filtered_space_slug_mapping,  # ID -> Slug mapping
            'total_spaces_from_api': len(space_list),  # Track original count for reference
            'empty_spaces_filtered': len(space_list) - len(spaces_with_audiences),  # Track how many were filtered
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
            'computed_traits': {
                'total': len(all_computed_traits),
                'enabled': len([ct for ct in all_computed_traits if ct['Enabled']]),
                'disabled': len([ct for ct in all_computed_traits if not ct['Enabled']]),
                'access_error': computed_traits_access_error
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

        # Computed Traits
        if all_computed_traits:
            with open(DATA_DIR / 'segment_computed_traits_audit.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_computed_traits[0].keys())
                writer.writeheader()
                writer.writerows(all_computed_traits)

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
            # Remove internal _destination_objects field before saving
            sources_data_clean = []
            for src in sources_data:
                src_copy = src.copy()
                src_copy.pop('_destination_objects', None)
                sources_data_clean.append(src_copy)

            with open(DATA_DIR / 'segment_sources_audit.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sources_data_clean[0].keys())
                writer.writeheader()
                writer.writerows(sources_data_clean)

        # Reverse ETL Models (save as JSON to preserve multi-line queries)
        if retl_models_data:
            with open(DATA_DIR / 'segment_retl_models.json', 'w', encoding='utf-8') as f:
                json.dump(retl_models_data, f, indent=2)

        # Warehouses (save as JSON to preserve nested settings)
        if warehouses_data:
            with open(DATA_DIR / 'segment_warehouses.json', 'w', encoding='utf-8') as f:
                json.dump(warehouses_data, f, indent=2)

        # Delivery Metrics (save as JSON)
        if delivery_metrics_data:
            with open(DATA_DIR / 'segment_delivery_metrics.json', 'w', encoding='utf-8') as f:
                json.dump(delivery_metrics_data, f, indent=2)
            print(f"Saved {len(delivery_metrics_data)} delivery metrics records")

        # Collect observability data (event volumes)
        audit_status['message'] = 'Collecting event volume data...'
        audit_status['progress'] = 95
        event_volume_data = {}
        try:
            from datetime import timedelta
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            fourteen_days_ago = now - timedelta(days=14)

            end_time = now.isoformat() + 'Z'
            seven_day_start = seven_days_ago.isoformat() + 'Z'
            fourteen_day_start = fourteen_days_ago.isoformat() + 'Z'

            # Get workspace volumes
            auditor = SegmentAuditor(api_token, workspace_id=workspace_id, skip_ssl_verify=skip_ssl_verify)
            seven_day_volume = auditor.get_event_volumes(seven_day_start, end_time, granularity='DAY')
            fourteen_day_volume = auditor.get_event_volumes(fourteen_day_start, end_time, granularity='DAY')
            seven_day_by_source = auditor.get_event_volumes(seven_day_start, end_time, granularity='DAY', group_by=['sourceId'])

            event_volume_data = {
                'seven_day': seven_day_volume,
                'fourteen_day': fourteen_day_volume,
                'seven_day_by_source': seven_day_by_source,
                'collection_time': now.isoformat()
            }

            # Save event volumes
            with open(DATA_DIR / 'segment_event_volumes.json', 'w', encoding='utf-8') as f:
                json.dump(event_volume_data, f, indent=2)

            # Add summary to audit_summary
            summary['observability'] = {
                'collected': True,
                'collection_time': now.isoformat()
            }
        except Exception as e:
            print(f"Warning: Could not fetch event volumes: {e}")
            event_volume_data = {}
            summary['observability'] = {
                'collected': False,
                'error': str(e)
            }

        # Add delivery metrics summary
        summary['delivery_metrics'] = {
            'collected': len(delivery_metrics_data) > 0,
            'total_connections': len(delivery_metrics_data),
            'time_range': '7 days',
            'granularity': 'DAY',
            'note': 'Direct connections only (excludes Engage and RETL/warehouse sources)' if len(delivery_metrics_data) > 0 else 'No data or insufficient permissions'
        }

        # Re-save summary with observability and delivery metrics data
        with open(DATA_DIR / 'audit_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

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

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'ok', 'service': 'segment-audit-dashboard'}), 200

@app.route('/run-audit', methods=['POST'])
def run_audit_route():
    """Start audit data collection"""
    global audit_status

    if audit_status['running']:
        return jsonify({'error': 'Audit already running'}), 400

    # Get form data
    api_token = request.form.get('api_token')
    gateway_token = request.form.get('gateway_token', '').strip()  # Optional
    skip_ssl = request.form.get('skip_ssl') == 'true'  # Checkbox returns 'true' or None

    # Validate
    if not api_token:
        return jsonify({'error': 'API token is required'}), 400

    # Store credentials in session for later use (workspace details will be fetched during audit)
    session.permanent = True  # Keep session alive for configured lifetime (7 days)
    session['api_token'] = api_token
    session['gateway_token'] = gateway_token if gateway_token else None
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
        args=(api_token, skip_ssl, gateway_token)
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
        session.permanent = True  # Extend session lifetime
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

@app.route('/audiences')
def audiences():
    """Audiences view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('dashboard.html', customer_name=customer_name)

@app.route('/dashboard')
def dashboard():
    """Legacy redirect to audiences"""
    return redirect('/audiences', code=301)

@app.route('/sources')
def sources():
    """Sources view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('sources.html', customer_name=customer_name)

@app.route('/computed-traits')
def computed_traits_view():
    """Computed traits view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('computed_traits.html', customer_name=customer_name)

@app.route('/observability')
def observability():
    """Observability view"""
    customer_name = session.get('customer_name', 'Customer')
    workspace_slug = session.get('workspace_slug', '')
    return render_template('observability.html', customer_name=customer_name, workspace_slug=workspace_slug)

@app.route('/connections')
def connections():
    """Connections view - Sankey diagram of source to destination flows"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('connections.html', customer_name=customer_name)

@app.route('/retl-models')
def retl_models():
    """Reverse ETL models view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('retl_models.html', customer_name=customer_name)

@app.route('/warehouses')
def warehouses():
    """Warehouses view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('warehouses.html', customer_name=customer_name)

@app.route('/ai-prompt')
def ai_prompt():
    """AI Prompt builder view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('ai-prompt.html', customer_name=customer_name)

@app.route('/proxy-logo')
def proxy_logo():
    """Proxy logos through our server to avoid CORS issues"""
    logo_url = request.args.get('url')
    if not logo_url:
        return "No URL provided", 400

    try:
        # Fetch the logo from the CDN
        # Disable SSL verification for logos as some CDNs have certificate issues
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(
            logo_url,
            timeout=5,
            verify=False,  # Disable SSL verification for logo CDNs
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )

        if response.status_code == 200:
            from flask import Response
            return Response(
                response.content,
                mimetype=response.headers.get('Content-Type', 'image/svg+xml'),
                headers={
                    'Cache-Control': 'public, max-age=86400',  # Cache for 24 hours
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            return f"Failed to fetch logo: {response.status_code}", 500
    except Exception as e:
        return f"Error: {str(e)}", 500

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

    # Load RETL models
    retl_models = []
    retl_file = DATA_DIR / 'segment_retl_models.json'
    if retl_file.exists():
        with open(retl_file, 'r', encoding='utf-8') as f:
            retl_models = json.load(f)

    # Load computed traits
    computed_traits = []
    computed_traits_file = DATA_DIR / 'segment_computed_traits_audit.csv'
    if computed_traits_file.exists():
        with open(computed_traits_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            computed_traits = list(reader)

    # Build markdown content
    audit_date = summary.get('audit_date', '')
    if audit_date:
        from datetime import datetime
        audit_date_obj = datetime.fromisoformat(audit_date)
        audit_date = audit_date_obj.strftime('%B %d, %Y at %I:%M %p')

    # Check if computed traits are accessible
    has_computed_traits_access = not summary.get('computed_traits', {}).get('access_error')

    # Build executive summary with conditional computed traits line
    computed_traits_line = ""
    if has_computed_traits_access:
        computed_traits_line = f"\n**Computed Traits:** {summary.get('computed_traits', {}).get('total', 0)} ({summary.get('computed_traits', {}).get('enabled', 0)} enabled)"

    md_content = f"""# {customer_name} - Segment Workspace Analysis

## Executive Summary

**Audit Date:** {audit_date}
**Workspace:** {workspace_slug}
**Total Sources:** {summary.get('sources', {}).get('total', 0)} ({summary.get('sources', {}).get('enabled', 0)} enabled)
**Total Audiences:** {summary.get('audiences', {}).get('total', 0)} ({summary.get('audiences', {}).get('enabled', 0)} enabled){computed_traits_line}
**Reverse ETL Models:** {len(retl_models)} ({len([m for m in retl_models if m.get('Enabled')])} enabled)
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

    md_content += "\n---\n\n## Reverse ETL Models\n\n"

    if retl_models:
        enabled_retl = [m for m in retl_models if m.get('Enabled')]
        disabled_retl = [m for m in retl_models if not m.get('Enabled')]

        md_content += f"This workspace has **{len(retl_models)} Reverse ETL models** configured to sync data from warehouses to downstream destinations.\n\n"
        md_content += f"- **Active Models:** {len(enabled_retl)} models currently syncing data\n"
        md_content += f"- **Inactive Models:** {len(disabled_retl)} models currently disabled\n\n"

        # Group by source
        retl_by_source = {}
        for model in retl_models:
            source_id = model.get('Source ID', '')
            if source_id not in retl_by_source:
                retl_by_source[source_id] = []
            retl_by_source[source_id].append(model)

        md_content += f"### Reverse ETL by Source\n\n"
        md_content += f"Models are distributed across **{len(retl_by_source)} warehouse source(s)**:\n\n"

        for source_id, models in retl_by_source.items():
            # Find source name
            source = next((s for s in sources if s.get('Source ID') == source_id), None)
            source_name = source.get('Source Name', source_id) if source else source_id

            enabled_count = len([m for m in models if m.get('Enabled')])
            md_content += f"- **{source_name}:** {len(models)} model(s) ({enabled_count} enabled)\n"

        md_content += f"\n### Active Reverse ETL Models\n\n"

        if enabled_retl:
            md_content += "The following models are actively syncing data:\n\n"
            for model in enabled_retl[:10]:  # Show top 10
                model_name = model.get('Name', 'Unnamed Model')
                source_id = model.get('Source ID', '')
                source = next((s for s in sources if s.get('Source ID') == source_id), None)
                source_name = source.get('Source Name', source_id) if source else source_id
                identifier = model.get('Query Identifier Column', 'N/A')

                md_content += f"#### {model_name}\n"
                md_content += f"- **Source:** {source_name}\n"
                md_content += f"- **Identifier Column:** `{identifier}`\n"

                # Add snippet of query (first 200 chars)
                query = model.get('Query', '')
                if query:
                    query_snippet = query[:200].replace('\n', ' ')
                    if len(query) > 200:
                        query_snippet += '...'
                    md_content += f"- **Query Preview:** `{query_snippet}`\n"

                md_content += "\n"

            if len(enabled_retl) > 10:
                md_content += f"\n_...and {len(enabled_retl) - 10} more active models_\n"
        else:
            md_content += "No active Reverse ETL models found.\n"
    else:
        md_content += "No Reverse ETL models configured in this workspace.\n"

    md_content += "\n---\n\n## Audience Segments\n\n"
    md_content += f"This workspace has **{len(audiences)} audience segments** defined for user targeting and personalization.\n\n"

    # Group audiences by status
    enabled_audiences = [a for a in audiences if a.get('Enabled', '').lower() == 'true']

    # Audience activation analysis (now available via Gateway API)
    audiences_with_destinations = [a for a in enabled_audiences if int(a.get('Destination Count', 0)) > 0]
    audiences_without_destinations = [a for a in enabled_audiences if int(a.get('Destination Count', 0)) == 0]

    md_content += f"### Audience Activation Summary\n\n"
    md_content += f"- **Total Active Audiences:** {len(enabled_audiences)}\n"
    if enabled_audiences:
        md_content += f"- **Activated to Destinations:** {len(audiences_with_destinations)} ({len(audiences_with_destinations)/len(enabled_audiences)*100:.1f}%)\n"
        md_content += f"- **Not Activated:** {len(audiences_without_destinations)} ({len(audiences_without_destinations)/len(enabled_audiences)*100:.1f}%)\n\n"

        if audiences_without_destinations:
            md_content += f"⚠️ **Note:** {len(audiences_without_destinations)} active audience(s) are not connected to any destinations. These audiences are defined but not being used for activation.\n\n"

    # Breakdown by destination count
    dest_counts = {}
    for aud in audiences:
        count = int(aud.get('Destination Count', 0))
        dest_counts[count] = dest_counts.get(count, 0) + 1

    if dest_counts:
        md_content += f"### Audiences by Destination Count\n\n"
        for count in sorted(dest_counts.keys(), reverse=True):
            audience_count = dest_counts[count]
            if count == 0:
                md_content += f"- **0 destinations:** {audience_count} audience(s) (not activated)\n"
            elif count == 1:
                md_content += f"- **1 destination:** {audience_count} audience(s)\n"
            else:
                md_content += f"- **{count} destinations:** {audience_count} audience(s)\n"
        md_content += "\n"

    md_content += f"### Active Audiences ({len(enabled_audiences)})\n\n"

    for audience in sorted(enabled_audiences, key=lambda x: int(x.get('Size', 0) or 0), reverse=True)[:20]:
        aud_name = audience.get('Name', '')
        aud_size = audience.get('Size', '0')
        aud_desc = audience.get('Description', 'No description')
        aud_query = audience.get('Definition Query', '')
        aud_destinations = audience.get('Connected Destinations', '')
        aud_dest_count = int(audience.get('Destination Count', 0))

        md_content += f"#### {aud_name}\n"
        md_content += f"- **Size:** {int(aud_size):,} users\n"
        md_content += f"- **Description:** {aud_desc}\n"

        # Connected destinations (now available via Gateway API)
        if aud_destinations:
            md_content += f"- **Connected Destinations ({aud_dest_count}):** {aud_destinations}\n"
        else:
            md_content += f"- **Connected Destinations:** None (not activated to any destinations)\n"

        # Add query definition (truncate if too long)
        if aud_query:
            query_snippet = aud_query[:300].replace('\n', ' ')
            if len(aud_query) > 300:
                query_snippet += '...'
            md_content += f"- **Query:** `{query_snippet}`\n"

        md_content += "\n"

    if len(enabled_audiences) > 20:
        md_content += f"\n_...and {len(enabled_audiences) - 20} more active audiences_\n"

    # Only include computed traits section if workspace has access
    if has_computed_traits_access:
        md_content += "\n---\n\n## Computed Traits\n\n"
        md_content += f"This workspace has **{len(computed_traits)} computed traits** that calculate and store user attributes based on event data and aggregations.\n\n"

        if computed_traits:
            # Count by type
            from collections import Counter
            type_counts = Counter()
            for ct in computed_traits:
                ct_type = ct.get('Type', 'Unknown')
                type_counts[ct_type] += 1

            md_content += "### Computed Trait Types\n\n"
            for ct_type, count in type_counts.most_common():
                md_content += f"- **{ct_type}:** {count} trait(s)\n"

            # Show active computed traits
            enabled_traits = [ct for ct in computed_traits if ct.get('Enabled', '').lower() == 'true']
            md_content += f"\n### Active Computed Traits ({len(enabled_traits)})\n\n"

            if enabled_traits:
                md_content += "The following traits are actively computing:\n\n"
                for ct in enabled_traits[:15]:  # Show top 15
                    ct_name = ct.get('Name', '')
                    ct_type = ct.get('Type', 'Unknown')
                    ct_def = ct.get('Definition', '')

                    md_content += f"#### {ct_name}\n"
                    md_content += f"- **Type:** {ct_type}\n"

                    # Show definition snippet (first 150 chars)
                    if ct_def:
                        def_snippet = ct_def[:150].replace('\n', ' ')
                        if len(ct_def) > 150:
                            def_snippet += '...'
                        md_content += f"- **Definition:** `{def_snippet}`\n"

                    md_content += "\n"

                if len(enabled_traits) > 15:
                    md_content += f"\n_...and {len(enabled_traits) - 15} more active computed traits_\n"
            else:
                md_content += "No active computed traits found.\n"
        else:
            md_content += "No computed traits configured in this workspace.\n"

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

    # Add Observability section
    md_content += "\n---\n\n## Event Volume & Observability\n\n"

    # Load event volume data
    event_volume_file = DATA_DIR / 'segment_event_volumes.json'
    if event_volume_file.exists():
        try:
            with open(event_volume_file, 'r', encoding='utf-8') as f:
                event_volumes = json.load(f)

            seven_day = event_volumes.get('seven_day', {}) if isinstance(event_volumes.get('seven_day'), dict) else {}
            fourteen_day = event_volumes.get('fourteen_day', {}) if isinstance(event_volumes.get('fourteen_day'), dict) else {}
            seven_day_by_source = event_volumes.get('seven_day_by_source', {}) if isinstance(event_volumes.get('seven_day_by_source'), dict) else {}

            # Calculate workspace-level totals - with validation
            seven_day_data = seven_day.get('data', []) if isinstance(seven_day.get('data'), list) else []
            fourteen_day_data = fourteen_day.get('data', []) if isinstance(fourteen_day.get('data'), list) else []
            seven_day_by_source_data = seven_day_by_source.get('data', []) if isinstance(seven_day_by_source.get('data'), list) else []

            seven_day_total = sum(day.get('value', 0) if isinstance(day, dict) else 0 for day in seven_day_data)
            fourteen_day_total = sum(day.get('value', 0) if isinstance(day, dict) else 0 for day in fourteen_day_data)

            md_content += f"### Workspace Event Volume\n\n"
            md_content += f"**Last 7 Days:** {seven_day_total:,} events\n\n"
            md_content += f"**Last 14 Days:** {fourteen_day_total:,} events\n\n"

            # Calculate daily averages
            if len(seven_day_data) > 0:
                daily_avg_7d = seven_day_total / len(seven_day_data)
                md_content += f"**Daily Average (7d):** {daily_avg_7d:,.0f} events/day\n\n"

            if len(fourteen_day_data) > 0:
                daily_avg_14d = fourteen_day_total / len(fourteen_day_data)
                md_content += f"**Daily Average (14d):** {daily_avg_14d:,.0f} events/day\n\n"

            # Analyze volume by source
            md_content += f"### Event Volume by Source\n\n"

            # Group by source and calculate totals
            source_volumes = {}
            for entry in seven_day_by_source_data:
                if isinstance(entry, dict):
                    source_id = entry.get('sourceId', 'Unknown')
                    volume = entry.get('value', 0)
                    if source_id not in source_volumes:
                        source_volumes[source_id] = 0
                    source_volumes[source_id] += volume

            # Sort by volume
            sorted_sources = sorted(source_volumes.items(), key=lambda x: x[1], reverse=True)

            if sorted_sources:
                md_content += "Sources ranked by 7-day event volume:\n\n"

                for source_id, volume in sorted_sources[:15]:  # Top 15 sources
                    # Find source name
                    source = next((s for s in sources if s.get('Source ID') == source_id), None)
                    source_name = source.get('Source Name', source_id) if source else source_id

                    # Calculate percentage of total
                    percentage = (volume / seven_day_total * 100) if seven_day_total > 0 else 0

                    md_content += f"- **{source_name}:** {volume:,} events ({percentage:.1f}%)\n"

                if len(sorted_sources) > 15:
                    remaining_volume = sum(v for _, v in sorted_sources[15:])
                    remaining_percentage = (remaining_volume / seven_day_total * 100) if seven_day_total > 0 else 0
                    md_content += f"\n_...and {len(sorted_sources) - 15} more source(s) with {remaining_volume:,} events ({remaining_percentage:.1f}%)_\n"

            # Identify low volume sources
            md_content += f"\n### Low Volume Sources\n\n"
            low_volume_threshold = 100  # Less than 100 events in 7 days
            low_volume_sources = [(sid, vol) for sid, vol in sorted_sources if vol < low_volume_threshold]

            if low_volume_sources:
                md_content += f"The following {len(low_volume_sources)} source(s) have very low event volume (< {low_volume_threshold} events in 7 days):\n\n"
                for source_id, volume in low_volume_sources[:10]:
                    source = next((s for s in sources if s.get('Source ID') == source_id), None)
                    source_name = source.get('Source Name', source_id) if source else source_id
                    md_content += f"- **{source_name}:** {volume:,} events\n"

                if len(low_volume_sources) > 10:
                    md_content += f"\n_...and {len(low_volume_sources) - 10} more low-volume source(s)_\n"

                md_content += "\n⚠️ **Note:** Low-volume sources may indicate data collection issues, testing sources, or sources that are no longer actively used.\n"
            else:
                md_content += "All sources have healthy event volumes.\n"

            # Analyze volume trends
            md_content += f"\n### Volume Trends\n\n"

            # Compare 7-day vs 14-day to detect trends
            if fourteen_day_total > 0 and seven_day_total > 0:
                # Calculate daily average for both periods
                seven_day_daily = seven_day_total / 7
                # For 14-day, we want the first 7 days (days 8-14)
                fourteen_day_daily = (fourteen_day_total - seven_day_total) / 7 if fourteen_day_total > seven_day_total else 0

                if fourteen_day_daily > 0:
                    change_pct = ((seven_day_daily - fourteen_day_daily) / fourteen_day_daily) * 100

                    if abs(change_pct) > 20:
                        trend = "significant increase" if change_pct > 0 else "significant decrease"
                        md_content += f"⚠️ **Volume Alert:** Event volume shows a **{trend}** of {abs(change_pct):.1f}% compared to the previous 7-day period.\n\n"

                        if change_pct < 0:
                            md_content += "This decline may indicate:\n"
                            md_content += "- Data collection issues\n"
                            md_content += "- Reduced user activity\n"
                            md_content += "- Sources being disabled or misconfigured\n"
                        else:
                            md_content += "This increase may indicate:\n"
                            md_content += "- New sources being enabled\n"
                            md_content += "- Increased user activity\n"
                            md_content += "- New tracking implementations\n"
                    elif abs(change_pct) < 5:
                        md_content += f"✅ Event volume is stable with only a {abs(change_pct):.1f}% change compared to the previous 7-day period.\n"
                    else:
                        trend_word = "increase" if change_pct > 0 else "decrease"
                        md_content += f"Event volume shows a moderate {trend_word} of {abs(change_pct):.1f}% compared to the previous 7-day period.\n"

            # Analyze daily volume variability (volatility)
            md_content += f"\n### Daily Volume Variability\n\n"

            if sorted_sources and len(sorted_sources) > 0:
                # Calculate volatility for each source
                source_volatility = []

                for source_id, _ in sorted_sources[:15]:  # Top 15 sources
                    source = next((s for s in sources if s.get('Source ID') == source_id), None)
                    source_name = source.get('Source Name', source_id) if source else source_id

                    # Get daily volumes for this source from seven_day_by_source
                    daily_volumes = []
                    for entry in seven_day_by_source_data:
                        if isinstance(entry, dict) and entry.get('sourceId') == source_id:
                            daily_volumes.append(entry.get('value', 0))

                    if len(daily_volumes) > 1:
                        # Calculate average and standard deviation
                        avg = sum(daily_volumes) / len(daily_volumes)
                        if avg > 0:
                            variance = sum((x - avg) ** 2 for x in daily_volumes) / len(daily_volumes)
                            std_dev = variance ** 0.5
                            coefficient_of_variation = (std_dev / avg) * 100  # Percentage

                            # Calculate max swing
                            max_swing = max(abs(x - avg) for x in daily_volumes) if daily_volumes else 0
                            max_swing_pct = (max_swing / avg * 100) if avg > 0 else 0

                            source_volatility.append({
                                'name': source_name,
                                'cv': coefficient_of_variation,
                                'max_swing_pct': max_swing_pct,
                                'avg': avg
                            })

                # Sort by coefficient of variation (highest variability first)
                source_volatility.sort(key=lambda x: x['cv'], reverse=True)

                if source_volatility:
                    md_content += "Sources with the highest day-to-day volume variability:\n\n"

                    for vol_data in source_volatility[:5]:  # Top 5 most volatile
                        md_content += f"- **{vol_data['name']}:** "
                        md_content += f"{vol_data['cv']:.1f}% variability, "
                        md_content += f"max swing ±{vol_data['max_swing_pct']:.1f}% from average\n"

                    md_content += "\n⚠️ **Note:** High variability may indicate:\n"
                    md_content += "- Batch processing or scheduled jobs\n"
                    md_content += "- Event-driven spikes (e.g., marketing campaigns, product launches)\n"
                    md_content += "- Data quality issues or intermittent collection problems\n"
                else:
                    md_content += "Volume variability analysis not available for this time period.\n"
            else:
                md_content += "Not enough data to analyze volume variability.\n"
        except Exception as obs_error:
            print(f"Error processing observability data: {obs_error}")
            md_content += f"\n⚠️ Error loading observability data: {str(obs_error)}\n"
        except Exception as obs_error:
            print(f"Error processing observability data: {obs_error}")
            md_content += f"\n⚠️ Error loading observability data: {str(obs_error)}\n"
    else:
        md_content += "Event volume data not available. This data is collected during workspace audits.\n"

    # Add detailed Engage/Personas sources analysis
    md_content += "\n### Engage Sources & Space Mapping\n\n"
    md_content += "**Note:** This workspace includes both custom sources (user-created) and Engage sources (system-generated by Segment's Personas/Engage product).\n\n"

    # Analyze Personas sources and group by space
    engage_sources = [s for s in sources if s.get('Is Engage')]
    total_engage_sources = len(engage_sources)

    if total_engage_sources > 0:
        # Group by space
        engage_by_space = {}
        unmapped_engage = []
        for source in engage_sources:
            space_name = source.get('Space')
            if space_name:
                if space_name not in engage_by_space:
                    engage_by_space[space_name] = []
                engage_by_space[space_name].append(source)
            else:
                unmapped_engage.append(source)

        md_content += f"**Total Engage Sources:** {total_engage_sources}\n\n"
        md_content += f"**Spaces with Engage Sources:** {len(engage_by_space)}\n\n"

        md_content += "#### 🔑 Key Understanding: Shadow Sources\n\n"
        md_content += "**Multiple Engage sources per space is NOT audience sprawl** - it's a technical architecture requirement called \"shadow sources\":\n\n"
        md_content += "- Segment's architecture allows **only one destination type per source**\n"
        md_content += "- When a Personas space sends audiences to multiple destination types (e.g., Facebook Ads, Google Ads, LinkedIn), Segment automatically creates multiple Engage sources\n"
        md_content += "- Each shadow source handles a different destination type\n"
        md_content += "- This is **by design** and indicates healthy multi-channel activation, not misconfiguration\n\n"

        if engage_by_space:
            md_content += "#### Engage Sources by Space:\n\n"
            for space_name in sorted(engage_by_space.keys()):
                sources_list = engage_by_space[space_name]
                md_content += f"**{space_name}** ({len(sources_list)} shadow source{'s' if len(sources_list) > 1 else ''}):\n"
                for source in sources_list:
                    dest_count = source.get('Destination Count', 0)
                    enabled = '✅' if source.get('Enabled') else '❌'
                    md_content += f"  - {enabled} `{source.get('Source Name')}` → {dest_count} destination(s)\n"
                md_content += "\n"

        if unmapped_engage:
            md_content += f"**Unmapped Engage Sources:** {len(unmapped_engage)} (unable to match to a space)\n\n"

        md_content += "#### Engage Source Insights:\n\n"
        md_content += "- The dashboard provides separate toggles on the **Observability** and **Connections** pages to view custom sources and Engage sources independently\n"
        md_content += "- Engage sources are automatically created when using Personas features like computed traits, audiences, and journeys\n"
        md_content += "- Each Engage source is mapped to its originating Personas space (shown in the **Space** column on the Sources page)\n"
        md_content += "- Engage sources typically represent outbound data flows from Personas to downstream destinations\n"
        md_content += "- **Volume from Engage sources reflects audience activation activity**, not raw event collection\n\n"
    else:
        md_content += "This workspace does not currently use Personas/Engage features.\n\n"

    # Add Delivery Metrics section
    md_content += "\n### Source-to-Destination Delivery Metrics\n\n"

    delivery_metrics_file = DATA_DIR / 'segment_delivery_metrics.json'
    if delivery_metrics_file.exists():
        try:
            with open(delivery_metrics_file, 'r', encoding='utf-8') as f:
                delivery_metrics_data = json.load(f)

            if delivery_metrics_data and len(delivery_metrics_data) > 0:
                md_content += f"**Overview:** Delivery performance metrics for {len(delivery_metrics_data)} source-destination connection(s) over the last 7 days.\n\n"
                md_content += "**Note:** RETL (warehouse) sources are excluded from delivery metrics for clarity. Only direct source-to-destination connections are included.\n\n"

                # Calculate summary statistics
                total_successes = 0
                total_retries = 0
                total_expired = 0
                total_discarded = 0
                connections_with_issues = []

                for pair in delivery_metrics_data:
                    metrics = pair.get('metrics', [])

                    successes = next((m.get('total', 0) for m in metrics if m.get('metricName') == 'successes'), 0)
                    retries = next((m.get('total', 0) for m in metrics if m.get('metricName') == 'retried'), 0)
                    expired = next((m.get('total', 0) for m in metrics if m.get('metricName') == 'expired'), 0)
                    discarded = next((m.get('total', 0) for m in metrics if m.get('metricName') == 'discarded'), 0)

                    total_successes += successes
                    total_retries += retries
                    total_expired += expired
                    total_discarded += discarded

                    if retries > 0 or expired > 0 or discarded > 0:
                        connections_with_issues.append({
                            'source': pair.get('source_name', ''),
                            'destination': pair.get('destination_name', ''),
                            'successes': successes,
                            'retries': retries,
                            'expired': expired,
                            'discarded': discarded
                        })

                # Summary metrics
                md_content += f"#### Summary (Last 7 Days)\n\n"
                md_content += f"- **Total Successful Deliveries:** {total_successes:,}\n"
                md_content += f"- **Total Retries:** {total_retries:,}\n"
                md_content += f"- **Expired Events:** {total_expired:,}\n"
                md_content += f"- **Discarded Events:** {total_discarded:,}\n"

                # Overall success rate
                total_events = total_successes + total_expired + total_discarded
                if total_events > 0:
                    success_rate = (total_successes / total_events) * 100
                    md_content += f"- **Overall Success Rate:** {success_rate:.2f}%\n"

                md_content += "\n"

                # Connections with issues
                if connections_with_issues:
                    md_content += f"#### ⚠️ Connections with Delivery Issues ({len(connections_with_issues)})\n\n"
                    md_content += "The following source-destination connections experienced retries, expirations, or discarded events:\n\n"

                    # Sort by severity (expired + discarded first, then retries)
                    connections_with_issues.sort(key=lambda x: (x['expired'] + x['discarded'], x['retries']), reverse=True)

                    for conn in connections_with_issues[:10]:  # Top 10 problematic connections
                        md_content += f"**{conn['source']} → {conn['destination']}**\n"
                        md_content += f"  - ✅ Successes: {conn['successes']:,}\n"
                        if conn['retries'] > 0:
                            md_content += f"  - 🔄 Retries: {conn['retries']:,}\n"
                        if conn['expired'] > 0:
                            md_content += f"  - ❌ Expired: {conn['expired']:,}\n"
                        if conn['discarded'] > 0:
                            md_content += f"  - ❌ Discarded: {conn['discarded']:,}\n"
                        md_content += "\n"

                    if len(connections_with_issues) > 10:
                        md_content += f"_...and {len(connections_with_issues) - 10} more connection(s) with issues_\n\n"

                    md_content += "**Possible Causes:**\n"
                    md_content += "- **Retries:** Temporary network issues, rate limiting, or destination API timeouts\n"
                    md_content += "- **Expired:** Events that couldn't be delivered within the retry window\n"
                    md_content += "- **Discarded:** Invalid data format, schema mismatches, or destination rejections\n\n"
                else:
                    md_content += "#### ✅ Delivery Health\n\n"
                    md_content += "All source-destination connections are delivering events successfully with no retries, expirations, or discarded events in the last 7 days.\n\n"

                # Detailed connection breakdown
                md_content += f"#### Detailed Connection Metrics\n\n"
                md_content += "Complete breakdown of all source-destination connections:\n\n"

                # Create comprehensive list with all metrics
                all_connections = []
                for pair in delivery_metrics_data:
                    metrics = pair.get('metrics', [])

                    success_metric = next((m for m in metrics if m.get('metricName') == 'successes'), {})
                    successes = success_metric.get('total', 0)
                    success_first = next((b.get('value', 0) for b in success_metric.get('breakdown', []) if b.get('metricName') == 'successes_on_first_attempt'), 0)
                    success_retry = next((b.get('value', 0) for b in success_metric.get('breakdown', []) if b.get('metricName') == 'successes_after_retry'), 0)

                    retries = next((m.get('total', 0) for m in metrics if m.get('metricName') == 'retried'), 0)
                    expired = next((m.get('total', 0) for m in metrics if m.get('metricName') == 'expired'), 0)
                    discarded = next((m.get('total', 0) for m in metrics if m.get('metricName') == 'discarded'), 0)

                    time_metric = next((m for m in metrics if m.get('metricName') == 'time_to_success'), {})
                    avg_latency = next((b.get('value', 0) for b in time_metric.get('breakdown', []) if b.get('metricName') == 'time_to_success_average'), 0)
                    p95_latency = next((b.get('value', 0) for b in time_metric.get('breakdown', []) if b.get('metricName') == 'time_to_success_p95'), 0)

                    total_attempts = successes + expired + discarded
                    success_rate = (successes / total_attempts * 100) if total_attempts > 0 else 0

                    all_connections.append({
                        'source': pair.get('source_name', ''),
                        'destination': pair.get('destination_name', ''),
                        'successes': successes,
                        'success_first': success_first,
                        'success_retry': success_retry,
                        'retries': retries,
                        'expired': expired,
                        'discarded': discarded,
                        'success_rate': success_rate,
                        'avg_latency': avg_latency,
                        'p95_latency': p95_latency,
                        'total_attempts': total_attempts
                    })

                # Sort by total volume (successes + failures)
                all_connections.sort(key=lambda x: x['total_attempts'], reverse=True)

                # Create markdown table
                md_content += "| Source | Destination | Success Rate | Successes | First Attempt | After Retry | Retries | Expired | Discarded | Avg Latency (ms) |\n"
                md_content += "|--------|-------------|-------------|-----------|---------------|-------------|---------|---------|-----------|------------------|\n"

                for conn in all_connections:
                    md_content += f"| {conn['source']} | {conn['destination']} | {conn['success_rate']:.1f}% | {conn['successes']:,} | {conn['success_first']:,} | {conn['success_retry']:,} | {conn['retries']:,} | {conn['expired']:,} | {conn['discarded']:,} | {int(conn['avg_latency'])} |\n"

                md_content += "\n"

                # Add insights section
                md_content += "#### Key Insights\n\n"

                # Highest success rate
                high_success = [c for c in all_connections if c['success_rate'] >= 99]
                if high_success:
                    md_content += f"**Excellent Performance ({len(high_success)} connections):** {len(high_success)} connection(s) have ≥99% success rate\n\n"

                # Connections needing attention
                needs_attention = [c for c in all_connections if c['success_rate'] < 95]
                if needs_attention:
                    md_content += f"**Needs Attention ({len(needs_attention)} connections):** The following connections have <95% success rate:\n\n"
                    for conn in needs_attention[:5]:
                        md_content += f"- **{conn['source']} → {conn['destination']}:** {conn['success_rate']:.1f}% success rate "
                        if conn['expired'] > 0:
                            md_content += f"({conn['expired']:,} expired) "
                        if conn['discarded'] > 0:
                            md_content += f"({conn['discarded']:,} discarded) "
                        md_content += "\n"
                    md_content += "\n"

                # High retry rate
                high_retry = [c for c in all_connections if c['retries'] > c['successes'] * 0.1]
                if high_retry:
                    md_content += f"**High Retry Rate ({len(high_retry)} connections):** These connections have significant retry activity:\n\n"
                    for conn in high_retry[:5]:
                        retry_pct = (conn['retries'] / conn['total_attempts'] * 100) if conn['total_attempts'] > 0 else 0
                        md_content += f"- **{conn['source']} → {conn['destination']}:** {retry_pct:.1f}% retry rate ({conn['retries']:,} retries)\n"
                    md_content += "\n"

                # Slow connections (high latency)
                slow_connections = [c for c in all_connections if c['avg_latency'] > 1000]
                if slow_connections:
                    md_content += f"**High Latency ({len(slow_connections)} connections):** These connections have >1 second average delivery time:\n\n"
                    for conn in sorted(slow_connections, key=lambda x: x['avg_latency'], reverse=True)[:5]:
                        md_content += f"- **{conn['source']} → {conn['destination']}:** {int(conn['avg_latency']):,}ms average latency\n"
                    md_content += "\n"
            else:
                md_content += "No delivery metrics data available. This may indicate no active source-destination connections during the collection period.\n\n"

        except Exception as e:
            print(f"Error loading delivery metrics: {e}")
            md_content += f"⚠️ Error loading delivery metrics data: {str(e)}\n\n"
    else:
        md_content += "Delivery metrics data not available. This data is collected during workspace audits.\n\n"

    md_content += "\n---\n\n## Recommendations for AI Analysis\n\n"
    md_content += """When analyzing this workspace, consider:

1. **Data Flow Patterns:** Examine which sources feed into which destinations to understand data routing
2. **Audience Strategy:** Review audience definitions and sizes to understand segmentation approach
3. **Event Coverage:** Look at which events are most frequently used in audiences to identify key behaviors
4. **Event Volume Health:** Analyze event volume trends and identify sources with low activity that may need attention
5. **Volume Distribution:** Review if event volume is concentrated in a few sources or well-distributed across the workspace
6. **Delivery Health:** Review the delivery metrics table to identify connections with high failure rates, retries, or latency issues
7. **Data Quality:** Check for empty audiences, disabled sources, or connections with high discard rates that may indicate data quality issues
8. **Use Case Alignment:** Evaluate if the current setup aligns with stated business objectives
9. **Performance Optimization:** Investigate connections with high retry rates or latency for potential infrastructure improvements
10. **Scaling Opportunities:** Identify underutilized destinations or audience patterns that could be expanded

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
        fourteen_days_ago = now - timedelta(days=14)

        # Format as ISO 8601
        end_time = now.isoformat() + 'Z'
        fourteen_day_start = fourteen_days_ago.isoformat() + 'Z'

        # Get 14-day volume grouped by sourceId (single API call for efficiency)
        # Frontend can filter this to 7 days if needed
        fourteen_day_by_source = auditor.get_event_volumes(fourteen_day_start, end_time, granularity='DAY', group_by=['sourceId'])

        return jsonify({
            'fourteen_day_by_source': fourteen_day_by_source
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
    """Reset audit status and clear session"""
    global audit_status
    audit_status = {
        'running': False,
        'progress': 0,
        'message': 'Ready',
        'complete': False,
        'error': None
    }
    # Clear session data
    session.clear()
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
        session.permanent = True  # Extend session lifetime
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
