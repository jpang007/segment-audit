# Export Fixes - Using Gateway API Schema Data

## Problem
The "Download All Files" export had issues with processed files:
1. **top_events.csv** was empty - using old `event_coverage.csv` file
2. **sources_with_destinations.csv** had blank "Top Events" column
3. Event volume data wasn't being extracted from Gateway API

## Root Cause
Export manager was looking for old Public API files (`event_coverage.csv`) instead of using the rich schema data available in `gateway_sources.json`.

## What We Fixed

### 1. Updated `export_top_events_csv()`
**Before:**
- Tried to read `event_coverage.csv` (Public API file)
- Returned empty/error

**After:**
- Reads `gateway_sources.json` 
- Extracts event schema with counts from each source
- Exports detailed event data:
  - Source Name
  - Event Name
  - Event Type (TRACK, PAGE, IDENTIFY)
  - 7-Day Volume (allowed)
  - Denied count
  - Total Events

**Output Example:**
```csv
Source Name,Event Name,Event Type,7-Day Volume,Denied,Total Events
axios_web_DEV,Page Viewed,PAGE,13826,0,13826
axios_web_DEV,IDENTIFY,IDENTIFY,7673,0,7673
axios_web_DEV,cta_click,TRACK,631,0,631
```

### 2. Updated `export_sources_with_destinations_csv()`
**Before:**
- Read from `gateway_sources.csv` (limited data)
- "Top Events" column was blank
- "7-Day Event Volume" was blank

**After:**
- Reads from `gateway_sources.json` (full schema data)
- Calculates total event volume per source
- Extracts top 10 events with counts
- Formats as: `"Event Name (count); Event Name (count); ..."`

**Output Example:**
```csv
Source Name,Source ID,Source Type,Enabled,Destinations Connected,Destination Names,Warehouses Connected,Warehouse Names,7-Day Event Volume,Top 10 Events (with counts)
axios_web_DEV,mx1txjHEHs5rhFWHrfy2U7,Javascript,true,5,"Braze, Amplitude, Facebook Pixel",0,"",24,373,"Page Viewed (13,826); IDENTIFY (7,673); cta_click (631); pageview (582); cta_variant_assignment_success (161)"
```

### 3. Data Source
Now uses `gateway_sources.json` which contains:
```json
{
  "name": "axios_web_DEV",
  "schema": {
    "events": [
      {
        "name": "Page Viewed",
        "type": "PAGE",
        "counts": {
          "allowed": 13826,
          "denied": 0
        }
      }
    ]
  }
}
```

## Files in ZIP Export

### Processed Folder (Analysis-Ready)
1. **sources_with_destinations.csv** - ✅ Now includes event volumes and top 10 events
2. **audiences_with_destinations.csv** - ✅ Works
3. **top_events.csv** - ✅ Now populated with all events across all sources

### Raw Data Folder
- All Gateway API files (JSON, CSV)
- Full schema data preserved

### For Gem Analysis Folder
- Formatted for AI analysis
- Includes full workspace context

## Testing

1. Go to http://localhost:5003/dashboard
2. Click "Download All Files" button
3. Extract the ZIP file
4. Check `processed/` folder:
   - **top_events.csv** should have rows with event names and volumes
   - **sources_with_destinations.csv** should have populated "Top 10 Events" column

## Expected Results

### Top Events CSV
Should show ~100+ events sorted by volume, with source names and counts.

### Sources with Destinations CSV
Each source should show:
- Total 7-day volume (e.g., "24,373")
- Top 10 events formatted like: "Page Viewed (13,826); IDENTIFY (7,673); cta_click (631)"

## Files Modified

- `/Users/jpang/segment-audit-dashboard/export_manager.py`
  - Rewrote `export_top_events_csv()` to use gateway_sources.json
  - Rewrote `export_sources_with_destinations_csv()` to extract schema data
  - Added event volume calculation logic
  - Added top 10 events extraction

