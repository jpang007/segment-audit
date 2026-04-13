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
