# Smart Export - Only Export What Was Collected

## Problem
The "Download All Files" export was including ALL possible files regardless of what data was actually collected during the audit. This was confusing and could fail if files didn't exist.

## Solution
Export now only includes files for data that was actually collected based on the checkboxes selected during audit setup.

## What Changed

### 1. Collection Metadata Storage
Added `collection_options` to `gateway_summary.json`:
```json
{
  "audit_date": "2026-06-01T...",
  "customer_name": "axios",
  "collection_options": {
    "sources": true,
    "destinations": true,
    "audiences": true,
    "journeys": true,
    "profiles": false,
    "mtu": false,
    "audit_trail": false,
    "usage_data": false,
    "fetch_definitions": false
  }
}
```

### 2. Conditional Export Logic
ExportManager now checks `collection_options` before including files:

**Sources with Destinations CSV:**
- Only included if `sources: true`
- Includes event schema data and top 10 events

**Top Events CSV:**
- Only included if `sources: true` (needs event schema)
- Shows all events across all sources with volumes

**Audiences with Destinations CSV:**
- Only included if `audiences: true`
- If `fetch_definitions: true`, could include more detail (future enhancement)

### 3. Smart README Summary
The README.txt in the ZIP now shows:

**DATA COLLECTED IN THIS AUDIT:**
```
   ✓ Sources & Event Schemas
   ✓ Destinations & Data Flows
   ✓ Audiences
   ✓ Journeys & Campaigns
```

Instead of always showing all possible options.

### 4. Processed Files List
Only lists files that were actually generated:
```
📂 /processed/ - Analysis-Ready Files
   ✓ sources_with_destinations.csv - Source connectivity & top events
   ✓ top_events.csv - Event volume analysis by source
   ✓ audiences_with_destinations.csv - Activation gap analysis
```

## Benefits

### 1. Clearer Exports
Users only get files for data they collected, avoiding confusion about missing or empty files.

### 2. Faster Exports
Don't waste time trying to export data that doesn't exist.

### 3. Accurate Documentation
README reflects what's actually in the ZIP, not what could potentially be there.

### 4. Future Enhancement Ready
If we add audience definition analysis, it can be conditional:
- If `fetch_definitions: false` → Basic audience export
- If `fetch_definitions: true` → Include events/traits used in definitions

## Example Scenarios

### Scenario 1: Minimal Audit (Audiences Only)
User selects:
- ✓ Audiences

Export includes:
- `processed/audiences_with_destinations.csv`
- `raw_data/gateway_audiences.csv`
- README mentions only audiences were collected

### Scenario 2: Full Audit
User selects:
- ✓ Sources
- ✓ Destinations
- ✓ Audiences
- ✓ Journeys
- ✓ MTU Data
- ✓ Audit Trail

Export includes:
- All processed CSVs
- All raw data files
- Complete README with all sections

### Scenario 3: Sources + Events Focus
User selects:
- ✓ Sources
- ✗ Everything else

Export includes:
- `processed/sources_with_destinations.csv` (with event data)
- `processed/top_events.csv` (event volume analysis)
- `raw_data/gateway_sources.json` (full schema)
- README showing only sources were collected

## Technical Details

### Session Storage
Collection options stored in Flask session:
```python
session['collect_options'] = {
    'sources': True,
    'destinations': True,
    # ...
}
session['fetch_definitions'] = False
```

### Export Manager
Loads options on init:
```python
def __init__(self, audit_data_dir):
    self.data_dir = Path(audit_data_dir)
    self.collection_options = self._load_collection_options()
```

Conditional export:
```python
if self.collection_options.get('sources', True):
    zip_file.writestr('processed/top_events.csv', ...)
```

## Files Modified

1. `/Users/jpang/segment-audit-dashboard/app.py`
   - Store `fetch_definitions` in session
   - Add `collection_options` to summary JSON

2. `/Users/jpang/segment-audit-dashboard/export_manager.py`
   - Load collection options from summary
   - Conditionally include processed files
   - Update README generation with collected data list
   - Smart processed files summary

## Testing

Run different audit combinations and verify exports:

1. **Audiences Only:**
   - Select only Audiences checkbox
   - Download export
   - Should only have audience files

2. **Sources + Destinations:**
   - Select Sources and Destinations
   - Download export
   - Should have source/destination files + top events

3. **Full Audit:**
   - Select all checkboxes
   - Download export
   - Should have all files

Each export's README should accurately reflect what was collected!

