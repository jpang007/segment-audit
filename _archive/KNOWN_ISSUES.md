# Known Issues and Behaviors

## Deleted Spaces Still Returned by API

**Issue:** The Segment Public API's `List Spaces` endpoint returns all spaces, including deleted ones.

**Behavior:**
- When a space is deleted in the Segment UI, it still appears in the API response
- Deleted spaces have no audiences, sources, or computed traits
- This causes the audit to show more spaces than are visible in the UI

**Solution Implemented:**
- The audit now filters out empty spaces (spaces with no audiences)
- Only spaces with at least one audience are included in the final dashboard
- The audit summary tracks:
  - `total_spaces_from_api`: Total spaces returned by the API
  - `empty_spaces_filtered`: Number of empty spaces filtered out
  - `space_ids`: Only active spaces with audiences

**Impact:**
- Progress messages during audit may show all spaces (e.g., "Collecting audiences from space 1/6")
- But the final dashboard only displays active spaces with content
- This is expected behavior and prevents confusion from seeing empty/deleted spaces

**Example:**
```
API returns: 6 spaces
Empty spaces: 2 (deleted but still in API)
Dashboard shows: 4 active spaces
```

## Warehouse Sync Reports - Rate Limiting

**Issue:** The `List Syncs from Warehouse` endpoint has a rate limit of 2 requests per minute.

**Behavior:**
- When collecting sync reports for multiple warehouses, the audit must wait 30 seconds between requests
- This is slower than other API calls but necessary to avoid 429 rate limit errors

**Solution Implemented:**
- No rate limiting delays added by default (fast collection)
- Frontend filters sync reports to last 24 hours for consistent display
- Each warehouse fetches up to 500 reports to ensure good coverage

**Impact:**
- Warehouse sync data collection is fast
- All warehouses show standardized 24-hour reporting window

## Source Name Mapping for Warehouse Syncs

**Behavior:**
- Warehouse sync reports contain `sourceId` but not source names
- The dashboard loads the sources CSV to map IDs to readable names
- If sources data is unavailable, sync reports show source IDs instead

**Solution:**
- Always run a full audit to ensure sources data is available
- The warehouse page automatically loads the sources mapping when available

## Audience Destinations - Feature Temporarily Disabled

**Status:** COMMENTED OUT - Not production-ready

**Reason:** The Segment Public API endpoint for audience-to-destination mapping (`GET /spaces/{spaceId}/audiences/{audienceId}/destinations`) is currently in Alpha testing and not available to all workspaces.

**Background:**
- This endpoint requires the Audience feature to be enabled in the workspace
- Alpha API access is not widely available
- Rate limit is only 50 requests/min (vs standard 100/min)
- May require special permissions from Segment customer success team

**Current Status:**
- Feature code is commented out in `app.py`
- CSV does not include "Connected Destinations" or "Destination Count" columns
- Markdown export does not include audience activation analysis

**Future Plans:**
- Re-enable when Segment releases this endpoint to general availability
- Alternative: Investigate GraphQL API for audience-destination mapping
- This feature is visible in the Segment UI, so the data exists - just need production-ready API access

**Workaround:**
- View audience destinations manually in the Segment UI
- Check the Connections page to see destination → audience mappings from the destination side

## Delivery Metrics - REST API Access

**Issue:** The delivery metrics feature uses the REST API endpoint `GET /destinations/{destinationId}/delivery-metrics`.

**Behavior:**
- During audit, the system collects delivery metrics for non-engage, non-warehouse source-destination pairs
- Uses the last 7 days with DAY granularity for daily trends
- RETL (warehouse) sources are excluded from delivery metrics for clearer visualization
- If the API token lacks permissions, the first request will return a 403 Forbidden error
- The audit automatically skips remaining delivery metrics collection and continues successfully
- No delivery metrics will be displayed on the Observability page or in the markdown export if collection fails

**API Endpoint:**
```
GET /destinations/{destinationId}/delivery-metrics
Query params: sourceId, startTime, endTime, granularity=DAY
Time range: Last 7 days
```

**Excluded Sources:**
- Engage/Personas sources (system-generated)
- Warehouse sources (RETL models) - excluded because the warehouse → model → destination relationship is complex to visualize

**Solution:**
- Delivery metrics are optional - the audit will complete successfully without them
- To enable delivery metrics, ensure your API token has access to the delivery-metrics endpoint
- Only direct source-to-destination connections are included in delivery metrics collection
- The feature gracefully degrades if permissions are insufficient

**Impact:**
- All other audit features work normally
- Event volumes, sources, audiences, and connections are not affected
- The observability page will show event volumes but not delivery metrics if collection fails
