# Export Formats Comparison

## Current Exports Overview

### 1. `gateway_sources.csv` (in ZIP /raw_data/)
**Created:** During audit  
**Size:** ~24KB  
**Format:** CSV with one row per source

**Columns:**
- Workspace, ID, Name, Slug, Status
- Type, Technical Type, Category
- Created At, Labels
- Connected Destinations, Destination Types
- Connected Warehouses, Warehouse Types  
- **Identify Traits** (comma-separated list)
- **Event Count** (total number of events)

**Example:**
```
Name,Event Count,Identify Traits
Edibles.com - Prod,9,"email,first_name,last_name"
```

**Use for:** Quick source inventory, filtering, basic analysis

---

### 2. `gateway_sources.json` (in ZIP /raw_data/)
**Created:** During audit  
**Size:** ~533KB (edible workspace)  
**Format:** JSON array of source objects with schemas

**Structure:**
```json
[
  {
    "id": "source_id",
    "name": "Edibles.com - Prod",
    "slug": "source-slug",
    "status": "ENABLED",
    "schema": {
      "events": [
        {
          "name": "Product Added",
          "type": "TRACK",
          "counts": {
            "allowed": 846,
            "denied": 0
          }
        }
      ]
    }
  }
]
```

**What it includes:**
- ✅ Full source metadata
- ✅ Event names
- ✅ Event types (TRACK, IDENTIFY, PAGE, SCREEN)
- ✅ Event counts (allowed/denied)
- ✅ Ready for programmatic analysis
- ❌ No individual property definitions
- ❌ No trait-level volume stats

**Use for:**
- Gem analysis (AI recommendations)
- Event catalog
- Event volume analysis
- Programmatic processing

---

### 3. Sources Page "Export to Excel" Button
**Created:** On-demand when you click export  
**Size:** Varies (detailed, ~100KB+ for small workspace)  
**Format:** Excel workbook with multiple sheets

**Sheets:**
1. **Master Data** - One row per event/trait
   - Source info repeated for each event
   - Event name, type, planning status
   - Allowed/denied counts (7-day window)
   - Trait names with volume stats

2. **Sources Summary** - One row per source
   - Total events, traits count
   - Total allowed/denied (aggregated)
   - Connected destinations/warehouses

**Example Master Data:**
```
source_name | object_name | object_type | allowed_7d | blocked_7d
Edibles.com | Product Added | TRACK | 846 | 0
Edibles.com | email | IDENTIFY | 173 | 0
```

**What it includes:**
- ✅ Flattened event-level data
- ✅ Individual trait rows
- ✅ 7-day volume windows
- ✅ Planning status (planned vs unplanned)
- ✅ Ready for pivot tables and Excel analysis
- ❌ Fetched live (slower, requires active session)

**Use for:**
- Excel analysis and pivot tables
- Detailed event volume review
- Sharing with non-technical stakeholders
- LLM analysis (flattened format)

---

## Key Differences

| Feature | CSV | JSON | Excel Export |
|---------|-----|------|--------------|
| **Event Names** | ❌ No | ✅ Yes | ✅ Yes (one row each) |
| **Event Counts** | ✅ Total only | ✅ Per event | ✅ Per event (7-day) |
| **Event Types** | ❌ No | ✅ Yes | ✅ Yes |
| **Properties** | ❌ No | ❌ No | ❌ No* |
| **Traits List** | ✅ Yes (aggregated) | ❌ No** | ✅ Yes (one row each) |
| **Trait Stats** | ❌ No | ❌ No | ✅ Yes (volumes) |
| **Format** | Flat CSV | Nested JSON | Flattened Excel |
| **Speed** | Fast (cached) | Fast (cached) | Slow (live fetch) |
| **Size** | Small | Medium | Medium-Large |
| **Best for** | Quick scan | API/Gem | Excel analysis |

\* Property definitions are not returned by the Gateway schema API  
\** Traits are in the schema but not surfaced in the events array

---

## What's Missing from gateway_sources.json

### 1. Trait-Level Data
The JSON has traits in `schema.collections[].objectProperties` but they're not easily accessible like the events array.

**Current structure (hidden in collections):**
```json
{
  "schema": {
    "collections": [
      {
        "name": "users",
        "objectProperties": [
          {
            "key": "email",
            "type": "string",
            "enabled": true,
            "stats": { "allowed": 173 }
          }
        ]
      }
    ]
  }
}
```

**Excel export has:** Individual trait rows with volume stats

### 2. Property Definitions
The Gateway API doesn't return property-level schemas (property names, types, descriptions for each event).

**What we have:**
```json
{
  "name": "Product Added",
  "counts": { "allowed": 846 }
}
```

**What we don't have:**
```json
{
  "name": "Product Added",
  "properties": {
    "product_id": { "type": "string" },
    "price": { "type": "number" },
    "quantity": { "type": "integer" }
  }
}
```

This data **may not be available** from the Gateway API at all.

---

## Why Different Formats?

### CSV - Quick Inventory
- One row per source
- Fast to scan
- Summarized data only
- No schema details

### JSON - Programmatic + Gem
- Complete source objects
- Event-level detail
- Ready for AI analysis
- Nested structure preserves relationships

### Excel - Human Analysis
- Flattened for pivot tables
- One row per event/trait
- Volume stats per object
- Planning status tracking
- Optimized for stakeholder sharing

---

## Recommendations

### For Technical Analysis
✅ Use `gateway_sources.json`
- Has all event names and counts
- Programmatically accessible
- Best for Gem upload

### For Business Stakeholders
✅ Use Sources page Excel export
- Flattened and easy to filter
- Individual event rows for pivot tables
- Planning status visible

### For Quick Scanning
✅ Use `gateway_sources.csv`
- Fast to open
- Good for filtering by status/type
- Event counts at a glance

---

## Could We Improve gateway_sources.json?

### Option 1: Flatten Traits into Events Array
Add traits as event-like objects:

```json
{
  "events": [
    { "name": "Product Added", "type": "TRACK", "counts": {...} },
    { "name": "email", "type": "IDENTIFY", "counts": {...} }
  ]
}
```

**Pros:** Everything in one array  
**Cons:** Mixing events and traits (different concepts)

### Option 2: Add Top-Level Traits Array
```json
{
  "schema": {
    "events": [...],
    "traits": [
      { "key": "email", "type": "string", "counts": {...} }
    ]
  }
}
```

**Pros:** Separate but accessible  
**Cons:** Requires parsing the collections to extract traits

### Option 3: Keep Current + Document Better
The current JSON **does have all the data** - it's just nested in `schema.collections[]`. Better documentation would help users find it.

---

## Current Status: ✅ Complete

The `gateway_sources.json` file **IS complete** with:
- ✅ 17 sources
- ✅ 147 track events with counts
- ✅ Event types (TRACK, IDENTIFY, etc.)
- ✅ Traits (in collections.users.objectProperties)
- ✅ Ready for Gem analysis

**What it doesn't have (and may not be available):**
- ❌ Individual property schemas per event
- ❌ Property types and descriptions
- ❌ Trait volumes exposed at top level

**Bottom line:** The JSON export has everything the Gateway API provides. Additional detail would require either:
1. Different API endpoints (may not exist)
2. Flattening existing data into different format
3. Multiple API calls per source (much slower)

---

## Your Question

> "how come it's different than the CSV that the sources page itself exports with the full schema and event counts"

**Answer:**

They serve different purposes:

1. **CSV in ZIP** = Summary view (one row per source, total event count)
2. **JSON in ZIP** = Complete schemas (all events with counts, nested format)
3. **Excel export** = Flattened analysis format (one row per event/trait)

The **JSON has MORE data** than the CSV, but in a different format than the Excel export.

All three formats have the same source data - just structured differently for different use cases.
