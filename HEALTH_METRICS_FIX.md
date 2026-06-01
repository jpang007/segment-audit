# Health Metrics Fix - Using HAR File Analysis

## Problem
Destinations page showed "No Data" for all health metrics, even though data exists in Segment UI.

## Root Cause
Our GraphQL query was missing **required** parameters that Segment's API needs:
1. `sourceId` was optional - should be **required** (`ID!`)
2. `destinationId` was optional - should be **required** (`String!`)

## What We Fixed

### 1. Updated GraphQL Query Structure
Changed from:
```graphql
query getDeliveryOverview(..., $sourceId: ID, $destinationId: String, ...)
```

To:
```graphql
query getDeliveryOverview(..., $sourceId: ID!, $destinationId: String!, ...)
```

### 2. Updated Function Signature
```python
# Before
def get_destination_delivery_metrics(self, destination_config_id, workspace_id, start_time, end_time, source_id=None, destination_metadata_id=None):

# After
def get_destination_delivery_metrics(self, destination_config_id, workspace_id, start_time, end_time, source_id, destination_metadata_id):
```

### 3. Added Required Parameter Validation
Now skips destinations that don't have both source_id and metadata_id:
```python
if not source_id or not metadata_id:
    print(f"    ⚠️  Skipping - missing source_id or metadata_id")
    # Set to no_data
    continue
```

### 4. Fixed Data Extraction from destinations.json
Now properly extracts:
- **source_id**: From `dest.source.id`
- **metadata_id**: From `dest.metadata.id`

Example for "[PROD] Sailthru V2 rETL":
- destinationConfigId: `6707be852dc8cc4c6e735793`
- sourceId: `szwsJDTWRDrJB3JFE7HhvE`
- destinationId (metadata): `5ee1302124d817af4c8341a2`

### 5. Added Loading Indicator
While metrics load, shows spinning "⟳" icon in health column.

## How HAR File Helped

Analyzed `/Users/jpang/Downloads/app.segment.com.har` to extract:
1. Exact GraphQL query Segment uses
2. Required vs optional parameters
3. Exact variable structure
4. Field names and nesting

## Testing

1. Go to http://localhost:5003/destinations
2. Watch for spinning ⟳ icon while loading
3. Should now show actual metrics for destinations with source connections
4. Check server logs at `/tmp/audit-server.log` for detailed output

## Expected Output in Logs

```
Starting to fetch metrics for 50 destinations...
  Fetching metrics for 6707be852dc8cc4c6e735793...
    Source ID: szwsJDTWRDrJB3JFE7HhvE, Metadata ID: 5ee1302124d817af4c8341a2
  Got response for 6707be852dc8cc4c6e735793: True
    Has deliveryOverview data
    Success: 2727, Failed: 0, Retries: 0
  ✓ 6707be852dc8cc4c6e735793: healthy (100.0%) - 2727 success, 0 failed
```

## Files Modified

1. `/Users/jpang/segment-audit-dashboard/app.py`
   - Updated `get_destination_delivery_metrics()` query
   - Made sourceId and destinationId required
   - Added parameter validation
   - Fixed data extraction

2. `/Users/jpang/segment-audit-dashboard/templates/gateway_destinations.html`
   - Added loading spinner animation
   - Shows ⟳ while metrics load
   - Shows ⋯ for pending data

