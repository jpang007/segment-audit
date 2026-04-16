#!/usr/bin/env python3
"""
Gateway API-Only Audit Dashboard
Testing Gateway API as replacement for Public API
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
import csv

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True

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

class GatewayAPIClient:
    """Gateway API GraphQL client"""

    def __init__(self, gateway_token, workspace_slug):
        self.gateway_token = gateway_token
        self.workspace_slug = workspace_slug
        self.base_url = "https://app.segment.com/gateway-api/graphql"
        self.headers = {
            "Authorization": f"Bearer {gateway_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-requested-with": "fetch"
        }

    def _execute_query(self, query, variables):
        """Execute a GraphQL query"""
        try:
            payload = {"query": query, "variables": variables}
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)

            data = response.json()

            if response.status_code == 401:
                raise Exception("Gateway API authentication failed. Token may be expired.")
            elif response.status_code != 200:
                # Try to get error details from response body
                print(f"\n=== HTTP {response.status_code} ERROR ===")
                print(f"Response: {json.dumps(data, indent=2)}")
                raise Exception(f"Gateway API returned {response.status_code}: {data}")

            if 'errors' in data:
                errors = data['errors']
                error_msg = errors[0].get('message', str(errors)) if errors else 'Unknown error'
                print(f"\n=== GraphQL ERROR ===")
                print(f"Message: {error_msg}")
                print(f"Full errors: {json.dumps(errors, indent=2)}")
                raise Exception(f"GraphQL error: {error_msg}")

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def get_workspace_connections(self):
        """Get all sources and destinations with connections"""
        query = """
        query getWorkspaceConnections($workspaceSlug: Slug!) {
          workspace(slug: $workspaceSlug) {
            id
            slug
            sources {
              id
              name
              slug
              status
              url
              connectedDestinations {
                id
                __typename
              }
              writeKeys
              flags {
                javascript
                __typename
              }
              settings
              metadata {
                id
                category
                name
                slug
                logos {
                  mark
                  default
                  __typename
                }
                type
                isCloudSource
                options
                __typename
              }
              __typename
            }
            destinations {
              id
              ... on Integration {
                name
                enabled
                __typename
                integrationStatus: status
                connectedSources {
                  id
                  __typename
                }
                metadata {
                  id
                  name
                  type
                  slug
                  logos {
                    mark
                    default
                    __typename
                  }
                  platforms {
                    server
                    browser
                    mobile
                    warehouse
                    __typename
                  }
                  integrationCategories: categories
                  __typename
                }
              }
              ... on Warehouse {
                name
                enabled
                __typename
                warehouseStatus: status
                connectedSources {
                  id
                  __typename
                }
                metadata {
                  id
                  name
                  slug
                  logos {
                    mark
                    default
                    __typename
                  }
                  __typename
                }
              }
              __typename
            }
            __typename
          }
        }
        """

        variables = {"workspaceSlug": self.workspace_slug}
        data = self._execute_query(query, variables)
        return data.get('workspace', {})

    def get_all_sources(self):
        """Get all sources with destinations via AllSources query"""
        query = """
        query AllSources($workspaceSlug: Slug!, $cursor: SourcesCursorInput!, $fetchStatus: Boolean!, $fetchDestinations: Boolean!) {
          workspace(slug: $workspaceSlug) {
            id
            sources: sourcesV2(cursor: $cursor) {
              data {
                id
                name
                slug
                status @include(if: $fetchStatus)
                createdAt
                flags {
                  javascript
                  autoInstrumentation
                  __typename
                }
                labels: labelsV2 {
                  key
                  value
                  __typename
                }
                metadata {
                  id
                  name
                  slug
                  logos {
                    mark
                    default
                    __typename
                  }
                  categories
                  category
                  isCloudEventSource
                  __typename
                }
                reverseEtlModels {
                  id
                  enabled
                  __typename
                }
                integrations @include(if: $fetchDestinations) {
                  id
                  name
                  metadata {
                    id
                    logos {
                      mark
                      default
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                warehouses @include(if: $fetchDestinations) {
                  id
                  name
                  metadata {
                    id
                    logos {
                      mark
                      default
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                __typename
              }
              cursor {
                next
                previous
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """

        variables = {
            "workspaceSlug": self.workspace_slug,
            "cursor": {"limit": 200},
            "fetchStatus": True,
            "fetchDestinations": True
        }

        data = self._execute_query(query, variables)
        workspace = data.get('workspace', {})
        sources_result = workspace.get('sources', {})
        return sources_result.get('data', [])

    def get_audiences_with_folders(self, space_id):
        """Get audiences with destinations via AudiencesAndFolders query with folder recursion"""
        query = """
        query AudiencesAndFolders($workspaceSlug: Slug!, $spaceId: String!, $cursor: RecordCursorInput!, $folderId: String) {
          workspace(slug: $workspaceSlug) {
            id
            space(id: $spaceId) {
              id
              audiencesAndFolders(cursor: $cursor, folderId: $folderId) {
                cursor {
                  limit
                  next
                  hasMore
                  __typename
                }
                data {
                  __typename
                  ... on Folder {
                    folderId: id
                    displayName
                    audienceCount
                  }
                  ... on Audience {
                    audienceId: id
                    key
                    name
                    enabled
                    collection
                    size
                    status
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

        audience_map = {}
        folders_to_process = []

        # Step 1: Get top-level items
        variables = {
            "workspaceSlug": self.workspace_slug,
            "spaceId": space_id,
            "cursor": {"limit": 200}
        }

        data = self._execute_query(query, variables)
        print(f"    DEBUG: Raw response keys: {data.keys() if data else 'None'}")
        workspace = data.get('workspace', {})
        print(f"    DEBUG: Workspace keys: {workspace.keys() if workspace else 'None'}")
        space = workspace.get('space', {})
        print(f"    DEBUG: Space keys: {space.keys() if space else 'None'}")
        audiences_and_folders = space.get('audiencesAndFolders', {})
        print(f"    DEBUG: audiencesAndFolders keys: {audiences_and_folders.keys() if audiences_and_folders else 'None'}")
        items = audiences_and_folders.get('data', [])
        print(f"    DEBUG: Found {len(items)} items (audiences + folders)")

        for item in items:
            typename = item.get('__typename', '')

            if typename == 'Folder':
                folder_id = item.get('folderId')
                folder_name = item.get('displayName', '')
                folder_count = item.get('audienceCount', 0)
                if folder_id and folder_count > 0:
                    folders_to_process.append({
                        'id': folder_id,
                        'name': folder_name,
                        'count': folder_count
                    })
            elif typename in ['Audience', 'RealtimeAudience']:
                audience_id = item.get('audienceId')
                if audience_id:
                    destinations = item.get('destinations', []) or []
                    audience_map[audience_id] = {
                        'id': audience_id,
                        'name': item.get('name', ''),
                        'key': item.get('key', ''),
                        'enabled': item.get('enabled', False),
                        'size': item.get('size', 0),
                        'collection': item.get('collection', ''),
                        'status': item.get('status', ''),
                        'destinations': [d.get('name', '') for d in destinations if d.get('name')],
                        'destination_count': len(destinations)
                    }

        # Step 2: Query each folder
        for folder in folders_to_process:
            variables = {
                "workspaceSlug": self.workspace_slug,
                "spaceId": space_id,
                "folderId": folder['id'],
                "cursor": {"limit": 200}
            }

            try:
                data = self._execute_query(query, variables)
                workspace = data.get('workspace', {})
                space = workspace.get('space', {})
                audiences_and_folders = space.get('audiencesAndFolders', {})
                items = audiences_and_folders.get('data', [])

                for item in items:
                    if item.get('__typename') in ['Audience', 'RealtimeAudience']:
                        audience_id = item.get('audienceId')
                        if audience_id:
                            destinations = item.get('destinations', []) or []
                            audience_map[audience_id] = {
                                'id': audience_id,
                                'name': item.get('name', ''),
                                'key': item.get('key', ''),
                                'enabled': item.get('enabled', False),
                                'size': item.get('size', 0),
                                'collection': item.get('collection', ''),
                                'status': item.get('status', ''),
                                'destinations': [d.get('name', '') for d in destinations if d.get('name')],
                                'destination_count': len(destinations),
                                'folder': folder['name']
                            }
            except Exception as e:
                print(f"Error fetching folder {folder['name']}: {e}")

        return list(audience_map.values())

    def get_spaces(self):
        """Get all spaces in workspace"""
        query = """
        query GetSpaces($workspaceSlug: Slug!) {
          workspace(slug: $workspaceSlug) {
            id
            spaces {
              id
              slug
              name
              __typename
            }
            __typename
          }
        }
        """

        variables = {"workspaceSlug": self.workspace_slug}
        data = self._execute_query(query, variables)
        workspace = data.get('workspace', {})
        return workspace.get('spaces', [])

    def get_source_schema(self, source_slug):
        """Get source event schema"""
        query = """
        query getSourceSchemaEvents($workspaceSlug: Slug!, $sourceSlug: String!, $timeframe: Int!, $useFlatClickHouseCounts: Boolean!) {
          workspace(slug: $workspaceSlug) {
            id
            source(slug: $sourceSlug) {
              id
              name
              events(days: $timeframe) @include(if: $useFlatClickHouseCounts) {
                name
                type
                counts @include(if: $useFlatClickHouseCounts) {
                  allowed
                  denied
                  __typename
                }
                __typename
              }
              schema {
                id
                collections {
                  id
                  name
                  events {
                    id
                    name
                    enabled
                    archived
                    createdAt
                    isPlanned
                    __typename
                  }
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """

        variables = {
            "workspaceSlug": self.workspace_slug,
            "sourceSlug": source_slug,
            "timeframe": 7,
            "useFlatClickHouseCounts": True
        }

        data = self._execute_query(query, variables)
        source = data.get('workspace', {}).get('source', {})

        return {
            'events': source.get('events', []),
            'collections': source.get('schema', {}).get('collections', [])
        }

    def get_audience_definition(self, space_id, audience_id):
        """Get audience definition"""
        query = """
        query GetAudienceDefinition($workspaceSlug: Slug!, $spaceId: String!, $audienceId: String!) {
          workspace(slug: $workspaceSlug) {
            space(id: $spaceId) {
              audience(id: $audienceId) {
                id
                name
                key
                engine
                status
                size
                createdAt
                definition {
                  type
                  options
                  __typename
                }
                __typename
              }
            }
          }
        }
        """

        variables = {
            "workspaceSlug": self.workspace_slug,
            "spaceId": space_id,
            "audienceId": audience_id
        }

        data = self._execute_query(query, variables)
        audience = data.get('workspace', {}).get('space', {}).get('audience', {})

        return {
            'audience': audience,
            'definition': audience.get('definition', {})
        }

    def get_journeys(self, space_id):
        """Get all journeys and campaigns for a space"""
        query = """
        query GetJourneys($workspaceSlug: Slug!, $spaceId: String!, $cursor: RecordCursorInput!) {
          workspace(slug: $workspaceSlug) {
            space(id: $spaceId) {
              campaignSearch(spaceId: $spaceId, cursor: $cursor) {
                cursor {
                  hasMore
                  next
                }
                data {
                  __typename
                  ... on Campaign {
                    containerId
                    version
                    versionCount
                    updatedAt
                    name
                    variant
                    state
                    definition
                    createdBy {
                      id
                      name
                    }
                    hasPublishedVersion
                    campaignsDestinations: destinations {
                      id
                      metadataId
                      name
                      logo
                    }
                  }
                  ... on Journey {
                    id
                    name
                    description
                    containerId
                    version
                    maxVersion
                    spaceId
                    executionState
                    status
                    emailActionCount
                    smsActionCount
                    whatsAppActionCount
                    mobilePushActionCount
                    destinations {
                      id
                      metadata {
                        ... on IntegrationMetadata {
                          id
                          name
                        }
                        ... on WarehouseMetadata {
                          id
                          name
                        }
                      }
                    }
                    createdBy {
                      id
                      name
                    }
                    updatedAt
                    container {
                      maxVersion
                      isLocked
                      updatedAt
                    }
                  }
                }
              }
            }
          }
        }
        """

        all_items = []
        next_cursor = None

        while True:
            variables = {
                "workspaceSlug": self.workspace_slug,
                "spaceId": space_id,
                "cursor": {
                    "limit": 200,
                    "next": next_cursor
                } if next_cursor else {
                    "limit": 200
                }
            }

            data = self._execute_query(query, variables)
            campaign_search = data.get('workspace', {}).get('space', {}).get('campaignSearch', {})

            if not campaign_search:
                break

            data_items = campaign_search.get('data', [])
            all_items.extend(data_items)

            cursor_info = campaign_search.get('cursor', {})
            has_more = cursor_info.get('hasMore', False)
            next_cursor = cursor_info.get('next')

            if not has_more or not next_cursor:
                break

        return all_items

    def get_identity_resolution_config(self, space_id):
        """Get identity resolution configuration for a space"""
        query = """
        query IdentityResolutionConfig($workspaceSlug: Slug!, $spaceId: String!) {
          workspace(slug: $workspaceSlug) {
            id
            space(id: $spaceId) {
              id
              identityResolutionConfig {
                idTypePriority
                externalIdConfigs {
                  id
                  idType
                  limit
                  mergedLimit
                  mergedLimitTimeRange
                  enforceUnique
                  seen
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """

        variables = {
            "workspaceSlug": self.workspace_slug,
            "spaceId": space_id
        }

        try:
            data = self._execute_query(query, variables)
            space_data = data.get('workspace', {}).get('space', {})

            if not space_data:
                print(f"    -> No space data returned for {space_id}")
                return []

            config = space_data.get('identityResolutionConfig', {})

            if not config:
                print(f"    -> No identityResolutionConfig found")
                return []

            # Get the priority order array
            id_type_priority = config.get('idTypePriority', [])
            configs = config.get('externalIdConfigs', [])

            # Add priority to each config based on its position in idTypePriority array
            for conf in configs:
                id_type = conf.get('idType', '')
                if id_type in id_type_priority:
                    conf['priority'] = id_type_priority.index(id_type) + 1  # 1-based priority
                else:
                    conf['priority'] = None

            # Sort by priority
            configs.sort(key=lambda x: x.get('priority') or 999)

            print(f"    -> Found {len(configs)} identity configs")
            if configs:
                print(f"    -> Full config data:")
                for conf in configs:
                    print(f"       {conf.get('idType')}: priority={conf.get('priority')}, limit={conf.get('limit')}, mergedLimit={conf.get('mergedLimit')}, mergedLimitTimeRange={conf.get('mergedLimitTimeRange')}")
            return configs
        except Exception as e:
            print(f"    -> Exception in get_identity_resolution_config: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_personas_data(self):
        """Get workspace-level personas/profiles entitlements"""
        query = """
        query PersonasData($workspaceSlug: Slug!) {
          workspace(slug: $workspaceSlug) {
            id
            entitiesEnabled: gateOpen(family: "releases", name: "entities")
            flags {
              canSeePersonas
              __typename
            }
            spaces {
              id
              slug
              __typename
            }
            billing {
              isFreeAccount
              __typename
            }
            entitlements {
              quotas {
                connections {
                  linkedEventsEntities
                  linkedEventsRows
                  __typename
                }
                __typename
              }
              features {
                personas
                profiles
                linkedAudiences
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """

        variables = {
            "workspaceSlug": self.workspace_slug
        }

        data = self._execute_query(query, variables)
        return data.get('workspace', {})

    def get_profiles_actions(self, space_id, action_type='VIOLATION', days_back=7):
        """Get profile actions (violations/errors) for a space"""
        query = """
        query personasProfilesActions($workspaceSlug: Slug!, $spaceId: String!, $filter: ProfilesActionsFilter!) {
          workspace(slug: $workspaceSlug) {
            id
            space(id: $spaceId) {
              id
              profilesActions(filter: $filter) {
                name
                messageId
                time
                type
                sourceId
                messageSentAt
                messageReceivedAt
                incomingEventType
                displayName
                messageSegmentId
                associatedProfileIds
                collection
                externalIds {
                  type
                  values
                  __typename
                }
                externalIdTypeCausingViolation
                droppedLink
                limitExceededTraits {
                  key
                  value
                  __typename
                }
                limitExceededEvents {
                  name
                  sourceId
                  __typename
                }
                droppedIdentifiers {
                  type
                  id
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """

        # Calculate time range (last N days)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)

        # Convert to milliseconds timestamp as strings
        end_ms = str(int(end_time.timestamp() * 1000))
        start_ms = str(int(start_time.timestamp() * 1000))

        variables = {
            "workspaceSlug": self.workspace_slug,
            "spaceId": space_id,
            "filter": {
                "action": {
                    "type": action_type
                },
                "startTime": start_ms,
                "endTime": end_ms
            }
        }

        data = self._execute_query(query, variables)
        space_data = data.get('workspace', {}).get('space', {})
        return space_data.get('profilesActions', [])

    def get_space_sources(self, space_id):
        """Get sources feeding into a specific space with destinations"""
        query = """
        query GetSpaceSources($workspaceSlug: Slug!, $spaceId: String!) {
          workspace(slug: $workspaceSlug) {
            id
            space(id: $spaceId) {
              id
              slug
              name
              sources {
                id
                name
                slug
                status
                metadata {
                  id
                  name
                  category
                  __typename
                }
                integrations {
                  id
                  name
                  __typename
                }
                warehouses {
                  id
                  name
                  __typename
                }
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """

        variables = {
            "workspaceSlug": self.workspace_slug,
            "spaceId": space_id
        }

        data = self._execute_query(query, variables)
        space_data = data.get('workspace', {}).get('space', {})
        return space_data.get('sources', [])


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page with Gateway token input"""
    return render_template('gateway_index.html')

@app.route('/start-audit', methods=['POST'])
def start_audit():
    """Start audit collection with Gateway API token"""
    try:
        data = request.json
        gateway_token = data.get('gateway_token', '').strip()
        workspace_slug = data.get('workspace_slug', '').strip()
        customer_name = data.get('customer_name', '').strip() or workspace_slug

        if not gateway_token or not workspace_slug:
            return jsonify({'error': 'Gateway token and workspace slug are required'}), 400

        # Store in session
        session['gateway_token'] = gateway_token
        session['workspace_slug'] = workspace_slug
        session['customer_name'] = customer_name
        session.permanent = True

        # Start audit in background
        import threading
        thread = threading.Thread(target=run_audit, args=(gateway_token, workspace_slug, customer_name))
        thread.daemon = True
        thread.start()

        return jsonify({'status': 'started'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_audit(gateway_token, workspace_slug, customer_name):
    """Run the audit collection"""
    global audit_status

    try:
        # Reset all status fields for new audit
        audit_status['running'] = True
        audit_status['progress'] = 0
        audit_status['message'] = 'Initializing Gateway API client...'
        audit_status['error'] = None
        audit_status['complete'] = False

        # Clear old audit data files
        for file_path in DATA_DIR.glob('gateway_*.csv'):
            file_path.unlink()
        for file_path in DATA_DIR.glob('gateway_*.json'):
            file_path.unlink()
        print("Cleared old audit data files")

        client = GatewayAPIClient(gateway_token, workspace_slug)

        # Get spaces
        audit_status['message'] = 'Fetching spaces...'
        audit_status['progress'] = 10
        spaces = client.get_spaces()
        print(f"Found {len(spaces)} spaces")

        # Get sources
        audit_status['message'] = 'Fetching sources...'
        audit_status['progress'] = 30
        sources = client.get_all_sources()
        print(f"Found {len(sources)} sources")

        # Get workspace connections
        audit_status['message'] = 'Fetching source-destination connections...'
        audit_status['progress'] = 50
        connections = client.get_workspace_connections()

        # Get audiences for each space
        audit_status['message'] = 'Collecting audiences...'
        audit_status['progress'] = 70
        all_audiences = []
        print(f"\n=== FETCHING AUDIENCES ===")
        print(f"Found {len(spaces)} spaces to query")
        for idx, space in enumerate(spaces):
            space_id = space.get('id')
            space_name = space.get('name', 'Unknown')
            print(f"\nQuerying space {idx + 1}/{len(spaces)}: {space_name} (ID: {space_id})")
            try:
                audiences = client.get_audiences_with_folders(space_id)
                print(f"  -> Returned {len(audiences)} audiences")
                for aud in audiences:
                    aud['space_id'] = space_id
                    aud['space_name'] = space_name
                    print(f"     - {aud.get('name', 'Unnamed')}")
                all_audiences.extend(audiences)
                print(f"  -> Total audiences so far: {len(all_audiences)}")
            except Exception as e:
                print(f"  -> ERROR: {e}")
                import traceback
                traceback.print_exc()

        # Get journeys for each space
        audit_status['message'] = 'Collecting journeys...'
        audit_status['progress'] = 80
        all_journeys = []
        print(f"\n=== FETCHING JOURNEYS ===")
        for idx, space in enumerate(spaces):
            space_id = space.get('id')
            space_name = space.get('name', 'Unknown')
            print(f"\nQuerying space {idx + 1}/{len(spaces)}: {space_name}")
            try:
                journeys = client.get_journeys(space_id)
                print(f"  -> Returned {len(journeys)} items (journeys + campaigns)")
                for journey in journeys:
                    journey['space_id'] = space_id
                    journey['space_name'] = space_name
                all_journeys.extend(journeys)
                print(f"  -> Total items so far: {len(all_journeys)}")
            except Exception as e:
                print(f"  -> ERROR: {e}")
                print(f"     (This may be normal if workspace doesn't have Engage feature)")

        # Get profile insights data
        audit_status['message'] = 'Collecting profile insights...'
        audit_status['progress'] = 85
        print(f"\n=== FETCHING PROFILE INSIGHTS ===")

        # Get workspace-level personas data
        personas_data = {}
        try:
            personas_data = client.get_personas_data()
            print(f"  -> Workspace entitlements: personas={personas_data.get('entitlements', {}).get('features', {}).get('personas')}, profiles={personas_data.get('entitlements', {}).get('features', {}).get('profiles')}")
        except Exception as e:
            print(f"  -> ERROR fetching personas data: {e}")

        # Get identity resolution config and space sources for each space
        all_identity_configs = []
        all_space_sources = []
        all_profile_violations = []
        for idx, space in enumerate(spaces):
            space_id = space.get('id')
            space_name = space.get('name', 'Unknown')
            print(f"\nQuerying identity config for space {idx + 1}/{len(spaces)}: {space_name}")
            try:
                configs = client.get_identity_resolution_config(space_id)
                if configs:
                    print(f"  -> Returned {len(configs)} external ID types")
                    for config in configs:
                        # Format the limit display
                        merged_limit = config.get('mergedLimit')
                        merged_time_range = config.get('mergedLimitTimeRange')
                        limit_display = config.get('limit', '')
                        seen = config.get('seen', False)

                        # If mergedLimit exists, show it with time range
                        if merged_limit and merged_time_range:
                            # Convert seconds to human readable format
                            seconds = int(merged_time_range)
                            if seconds == 86400:  # 1 day
                                time_period = "daily"
                            elif seconds == 604800:  # 7 days
                                time_period = "weekly"
                            elif seconds == 2592000:  # 30 days
                                time_period = "monthly"
                            elif seconds == 31536000:  # 365 days
                                time_period = "annually"
                            else:
                                # Calculate days if not a standard period
                                days = seconds // 86400
                                time_period = f"{days} days"

                            limit_display = f"{merged_limit} {time_period}"
                        elif merged_limit:
                            limit_display = f"{merged_limit} ever"

                        all_identity_configs.append({
                            'space_id': space_id,
                            'space_name': space_name,
                            'id_type': config.get('idType', ''),
                            'priority': config.get('priority', ''),
                            'limit': limit_display,
                            'seen': 'Yes' if seen else 'No'
                        })
                else:
                    print(f"  -> No identity configs returned")
            except Exception as e:
                print(f"  -> ERROR fetching identity config: {e}")
                import traceback
                traceback.print_exc()

            # Get sources for this space
            try:
                space_sources = client.get_space_sources(space_id)
                print(f"  -> Returned {len(space_sources)} sources")
                for source in space_sources:
                    # Extract destination names from integrations and warehouses
                    destinations = []
                    for integration in source.get('integrations', []):
                        if integration.get('name'):
                            destinations.append(integration['name'])
                    for warehouse in source.get('warehouses', []):
                        if warehouse.get('name'):
                            destinations.append(warehouse['name'])

                    all_space_sources.append({
                        'space_id': space_id,
                        'space_name': space_name,
                        'source_id': source.get('id', ''),
                        'source_name': source.get('name', ''),
                        'source_status': source.get('status', ''),
                        'source_type': source.get('metadata', {}).get('name', ''),
                        'source_category': source.get('metadata', {}).get('category', ''),
                        'destinations': ', '.join(destinations) if destinations else ''
                    })
            except Exception as e:
                print(f"  -> ERROR fetching space sources: {e}")

            # Get profile violations for this space (last 7 days)
            try:
                violations = client.get_profiles_actions(space_id, 'VIOLATION', days_back=7)
                print(f"  -> Returned {len(violations)} profile violations (last 7 days)")

                # Limit to most recent 100 violations per space to avoid overwhelming data
                violations_to_process = violations[:100] if len(violations) > 100 else violations
                if len(violations) > 100:
                    print(f"  -> Limiting to most recent 100 violations (had {len(violations)} total)")

                for violation in violations_to_process:
                    # Extract relevant violation details
                    external_ids = violation.get('externalIds', [])
                    external_id_str = ', '.join([f"{eid.get('type')}={','.join(eid.get('values', []))}" for eid in external_ids])

                    dropped_identifiers = violation.get('droppedIdentifiers', [])
                    dropped_ids_str = ', '.join([f"{did.get('type')}={did.get('id', '')}" for did in dropped_identifiers])

                    limit_exceeded_events = violation.get('limitExceededEvents', [])
                    exceeded_events_str = ', '.join([evt.get('name', '') for evt in limit_exceeded_events])

                    all_profile_violations.append({
                        'space_id': space_id,
                        'space_name': space_name,
                        'type': violation.get('type', ''),
                        'time': violation.get('time', ''),
                        'source_id': violation.get('sourceId', ''),
                        'incoming_event_type': violation.get('incomingEventType', ''),
                        'external_ids': external_id_str,
                        'violation_type': violation.get('externalIdTypeCausingViolation', ''),
                        'dropped_identifiers': dropped_ids_str,
                        'exceeded_events': exceeded_events_str
                    })
            except Exception as e:
                print(f"  -> ERROR fetching profile violations: {e}")
                import traceback
                traceback.print_exc()

        # Save data
        audit_status['message'] = 'Saving audit data...'
        audit_status['progress'] = 90

        # Save sources CSV
        if sources:
            with open(DATA_DIR / 'gateway_sources.csv', 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['ID', 'Name', 'Slug', 'Status', 'Type', 'Category', 'Created At', 'Labels', 'Connected Destinations', 'Connected Warehouses']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for source in sources:
                    labels = ', '.join([f"{l['key']}={l['value']}" for l in source.get('labels', [])])
                    integrations = ', '.join([i.get('name', '') for i in source.get('integrations', [])])
                    warehouses = ', '.join([w.get('name', '') for w in source.get('warehouses', [])])

                    writer.writerow({
                        'ID': source.get('id', ''),
                        'Name': source.get('name', ''),
                        'Slug': source.get('slug', ''),
                        'Status': source.get('status', ''),
                        'Type': source.get('metadata', {}).get('name', ''),
                        'Category': source.get('metadata', {}).get('category', ''),
                        'Created At': source.get('createdAt', ''),
                        'Labels': labels,
                        'Connected Destinations': integrations,
                        'Connected Warehouses': warehouses
                    })

        # Save audiences CSV
        if all_audiences:
            with open(DATA_DIR / 'gateway_audiences.csv', 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['ID', 'Name', 'Key', 'Enabled', 'Size', 'Space', 'Space ID', 'Folder', 'Destinations', 'Destination Count']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for aud in all_audiences:
                    writer.writerow({
                        'ID': aud.get('id', ''),
                        'Name': aud.get('name', ''),
                        'Key': aud.get('key', ''),
                        'Enabled': aud.get('enabled', False),
                        'Size': aud.get('size', 0),
                        'Space': aud.get('space_name', ''),
                        'Space ID': aud.get('space_id', ''),
                        'Folder': aud.get('folder', ''),
                        'Destinations': ', '.join(aud.get('destinations', [])),
                        'Destination Count': aud.get('destination_count', 0)
                    })

        # Save journeys CSV
        if all_journeys:
            with open(DATA_DIR / 'gateway_journeys.csv', 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Type', 'ID', 'Name', 'Description', 'State', 'Status', 'Space', 'Space ID',
                             'Current Version', 'Max Version', 'Destinations', 'Destination Count',
                             'Created By', 'Updated At']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for item in all_journeys:
                    typename = item.get('__typename', '')

                    if typename == 'Journey':
                        destinations = []
                        for dest in item.get('destinations', []):
                            metadata = dest.get('metadata', {})
                            if metadata and isinstance(metadata, dict):
                                destinations.append(metadata.get('name', ''))

                        dest_list = ', '.join(destinations)

                        writer.writerow({
                            'Type': 'Journey',
                            'ID': item.get('id', ''),
                            'Name': item.get('name', ''),
                            'Description': item.get('description', ''),
                            'State': item.get('status', ''),
                            'Status': item.get('executionState', ''),
                            'Space': item.get('space_name', ''),
                            'Space ID': item.get('space_id', ''),
                            'Current Version': item.get('version', ''),
                            'Max Version': item.get('maxVersion', ''),
                            'Destinations': dest_list,
                            'Destination Count': len(destinations),
                            'Created By': item.get('createdBy', {}).get('name', ''),
                            'Updated At': item.get('updatedAt', '')
                        })

                    elif typename == 'Campaign':
                        destinations = [d.get('name', '') for d in item.get('campaignsDestinations', [])]
                        dest_list = ', '.join(destinations)

                        state = 'published' if item.get('hasPublishedVersion') else 'draft'

                        writer.writerow({
                            'Type': 'Campaign',
                            'ID': item.get('containerId', ''),
                            'Name': item.get('name', ''),
                            'Description': '',
                            'State': state,
                            'Status': item.get('state', ''),
                            'Space': item.get('space_name', ''),
                            'Space ID': item.get('space_id', ''),
                            'Current Version': item.get('version', ''),
                            'Max Version': item.get('versionCount', ''),
                            'Destinations': dest_list,
                            'Destination Count': len(destinations),
                            'Created By': item.get('createdBy', {}).get('name', ''),
                            'Updated At': item.get('updatedAt', '')
                        })

        # Save profile insights data (always create file even if empty)
        with open(DATA_DIR / 'gateway_profile_insights.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Space', 'Space ID', 'ID Type', 'Priority', 'Limit', 'Seen']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for config in all_identity_configs:
                writer.writerow({
                    'Space': config.get('space_name', ''),
                    'Space ID': config.get('space_id', ''),
                    'ID Type': config.get('id_type', ''),
                    'Priority': config.get('priority', ''),
                    'Limit': config.get('limit', ''),
                    'Seen': config.get('seen', 'No')
                })

        print(f"\nSaved {len(all_identity_configs)} identity configs to CSV")

        # Save space sources data (always create file even if empty)
        with open(DATA_DIR / 'gateway_space_sources.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Space', 'Space ID', 'Source Name', 'Status', 'Type', 'Category', 'Destinations']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for source in all_space_sources:
                writer.writerow({
                    'Space': source.get('space_name', ''),
                    'Space ID': source.get('space_id', ''),
                    'Source Name': source.get('source_name', ''),
                    'Status': source.get('source_status', ''),
                    'Type': source.get('source_type', ''),
                    'Category': source.get('source_category', ''),
                    'Destinations': source.get('destinations', '')
                })

        print(f"Saved {len(all_space_sources)} space sources to CSV")

        # Save profile violations data (always create file even if empty)
        with open(DATA_DIR / 'gateway_profile_violations.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Space', 'Space ID', 'Type', 'Time', 'Source ID', 'Event Type', 'External IDs', 'Violation Type', 'Dropped Identifiers', 'Exceeded Events']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for violation in all_profile_violations:
                writer.writerow({
                    'Space': violation.get('space_name', ''),
                    'Space ID': violation.get('space_id', ''),
                    'Type': violation.get('type', ''),
                    'Time': violation.get('time', ''),
                    'Source ID': violation.get('source_id', ''),
                    'Event Type': violation.get('incoming_event_type', ''),
                    'External IDs': violation.get('external_ids', ''),
                    'Violation Type': violation.get('violation_type', ''),
                    'Dropped Identifiers': violation.get('dropped_identifiers', ''),
                    'Exceeded Events': violation.get('exceeded_events', '')
                })

        print(f"Saved {len(all_profile_violations)} profile violations to CSV")

        # Save personas entitlements
        with open(DATA_DIR / 'gateway_personas_entitlements.json', 'w') as f:
            json.dump(personas_data, f, indent=2)

        # Save summary
        summary = {
            'audit_date': datetime.now().isoformat(),
            'customer_name': customer_name,
            'workspace_slug': workspace_slug,
            'sources_count': len(sources),
            'audiences_count': len(all_audiences),
            'journeys_count': len([j for j in all_journeys if j.get('__typename') == 'Journey']),
            'campaigns_count': len([j for j in all_journeys if j.get('__typename') == 'Campaign']),
            'spaces_count': len(spaces)
        }

        with open(DATA_DIR / 'gateway_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        audit_status['complete'] = True
        audit_status['progress'] = 100
        audit_status['message'] = 'Audit complete!'

    except Exception as e:
        audit_status['error'] = str(e)
        audit_status['message'] = f'Error: {str(e)}'
        print(f"Audit error: {e}")
    finally:
        audit_status['running'] = False

@app.route('/audit-status')
def get_audit_status():
    """Get current audit status"""
    return jsonify(audit_status)

@app.route('/progress')
def progress():
    """Progress page"""
    return render_template('gateway_progress.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard with both sources and audiences"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('gateway_dashboard.html', customer_name=customer_name)

@app.route('/sources')
def sources():
    """Sources view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('gateway_sources.html', customer_name=customer_name)

@app.route('/audiences')
def audiences():
    """Audiences view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('gateway_audiences.html', customer_name=customer_name)

@app.route('/journeys')
def journeys():
    """Journeys view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('gateway_journeys.html', customer_name=customer_name)

@app.route('/profile-insights')
def profile_insights():
    """Profile Insights view"""
    customer_name = session.get('customer_name', 'Customer')
    return render_template('gateway_profile_insights.html', customer_name=customer_name)

@app.route('/audit_data/<path:filename>')
def serve_data(filename):
    """Serve audit data files"""
    file_path = DATA_DIR / filename
    if file_path.exists():
        from flask import send_file
        return send_file(file_path)
    return f"File not found: {filename}", 404

@app.route('/api/source-schema/<source_slug>')
def get_source_schema_api(source_slug):
    """Get source event schema via Gateway API"""
    try:
        gateway_token = session.get('gateway_token')
        workspace_slug = session.get('workspace_slug')

        if not gateway_token or not workspace_slug:
            return jsonify({'error': 'Session expired. Please run a new audit.'}), 401

        client = GatewayAPIClient(gateway_token, workspace_slug)
        schema_data = client.get_source_schema(source_slug)

        return jsonify(schema_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audience-definition/<space_id>/<audience_id>')
def get_audience_definition_api(space_id, audience_id):
    """Get audience definition via Gateway API"""
    try:
        gateway_token = session.get('gateway_token')
        workspace_slug = session.get('workspace_slug')

        if not gateway_token or not workspace_slug:
            return jsonify({'error': 'Session expired. Please run a new audit.'}), 401

        client = GatewayAPIClient(gateway_token, workspace_slug)
        definition_data = client.get_audience_definition(space_id, audience_id)

        return jsonify(definition_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset')
def reset():
    """Reset and start new audit"""
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))

    print("="*80)
    print("Gateway API Audit Dashboard")
    print("="*80)
    print()
    print("🚀 Starting server...")
    print(f"📁 Data directory: {DATA_DIR}")
    print()
    print(f"📊 Dashboard URL: http://localhost:{port}")
    print()
    print("💡 This version uses Gateway API (GraphQL)")
    print("💡 Press Ctrl+C to stop the server")
    print("="*80)
    print()

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
