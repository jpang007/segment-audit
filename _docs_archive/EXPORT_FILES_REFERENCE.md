# Segment Audit Dashboard - Export Files Reference

## Complete Export Contents

When you click **"📦 Download All Files"**, you get a ZIP with the following structure:

---

## 📂 /processed/ - Analysis-Ready CSVs

### `sources_with_destinations.csv`
**What it is:** All sources with their connected destinations and warehouses  
**Columns:**
- Source Name, ID, Type, Status
- Connected Destinations (name + type)
- Connected Warehouses (name + type)
- 7-Day Event Volume (if available)
- Top Events

**Use for:**
- Quick source connectivity audit
- Finding sources without destinations
- Identifying disabled sources

---

### `audiences_with_destinations.csv`
**What it is:** All audiences with activation status  
**Columns:**
- Audience Name, ID, Space
- Size, Enabled status
- Destinations Connected (count + names)
- Destination Types
- Use Case Recommendation (auto-generated)

**Use for:**
- Finding activation gaps (audiences with 0 destinations)
- Prioritizing high-value audiences
- Workspace hygiene (empty or disabled audiences)

---

### `top_events.csv`
**What it is:** Event usage analysis  
**Columns:**
- Event Name
- Used in Audiences (Yes/No)
- Audience Count
- Priority (HIGH/MEDIUM/LOW/UNUSED)
- Recommended Actions

**Use for:**
- Identifying high-value events
- Finding unused events to build audiences from

---

## 📂 /raw_data/ - Complete Raw Data

### `gateway_sources.csv`
**What it is:** Basic source information  
**Columns:**
- Workspace, ID, Name, Slug, Status
- Type, Technical Type, Category
- Created At, Labels
- Connected Destinations, Destination Types
- Connected Warehouses, Warehouse Types
- Identify Traits (comma-separated list)
- Event Count

**Use for:**
- Spreadsheet analysis
- Filtering by source type or status
- Quick trait reference

---

### `gateway_sources.json` ⭐
**What it is:** **FULL SOURCE SCHEMAS** with all events, properties, and traits  
**Structure:**
```json
[
  {
    "id": "source_id",
    "name": "Source Name",
    "slug": "source-slug",
    "status": "ENABLED",
    "schema": {
      "collections": [
        {
          "name": "track",
          "events": [
            {
              "name": "Product Viewed",
              "properties": {
                "product_id": { "type": "string" },
                "price": { "type": "number" }
              }
            }
          ]
        },
        {
          "name": "users",
          "objectProperties": [
            {
              "key": "email",
              "type": "string",
              "enabled": true
            }
          ]
        }
      ]
    }
  }
]
```

**Use for:**
- Complete event catalog
- Property definitions and types
- Event volume analysis
- Schema drift detection
- Data governance
- **Gem analysis** (automatically included in workspace_audit_data.json)

---

### `gateway_audiences.csv`
**What it is:** All audiences with metadata  
**Columns:**
- Workspace, ID, Name, Key
- Enabled, Size, Space, Space ID
- Folder (if organized)
- Destinations, Destination Count
- Definition (if fetched)

**Use for:**
- Audience inventory
- Finding unorganized audiences
- Size distribution analysis

---

### `gateway_destinations.json`
**What it is:** All destinations with configurations  
**Structure:**
```json
[
  {
    "id": "dest_id",
    "name": "Destination Name",
    "type": "Google Analytics 4",
    "enabled": true,
    "settings": { ... },
    "connectedSources": [...],
    "connectedAudiences": [...]
  }
]
```

**Use for:**
- Destination inventory
- Configuration audit
- Finding unused destinations

---

### `gateway_mtu.json`
**What it is:** MTU/API usage data with billing info  
**Structure:**
```json
{
  "billing": {
    "planName": "Business",
    "isOnApiPlan": true,
    "isOnMtuPlan": false,
    "quota": { "calls": 120000000 },
    "usage": { "mtus": { "users": 1250, "anonymous": 52735 } }
  },
  "historicalBilling": [
    {
      "planName": "Business",
      "start": "2026-04-01",
      "end": "2026-05-01",
      "usage": { "mtus": { "users": 319050, "anonymous": 24625948 } }
    }
  ]
}
```

**Use for:**
- Usage trending
- Plan compliance
- Monthly comparison

---

### `gateway_usage_data.json`
**What it is:** Detailed workspace entitlements and features  
**Includes:**
- Feature flags (Engage, Unify, Protocols, etc.)
- Quotas (API calls, MTU, Reverse ETL rows, etc.)
- Billing period and plan details

---

### `gateway_audit_trail.json`
**What it is:** Workspace activity logs  
**Includes:**
- User actions (created, updated, deleted)
- Timestamps and user emails
- Object types (sources, destinations, audiences, etc.)

**Use for:**
- Activity analysis
- Change tracking
- Compliance reporting

---

### `gateway_profile_insights.csv`
**What it is:** Identity resolution configuration per space  
**Columns:**
- Space, Space ID
- External ID types configured
- Resolution settings

---

### `gateway_space_sources.csv`
**What it is:** Sources connected to each Engage space  
**Columns:**
- Space, Space ID
- Connected Source IDs and Names

---

### `gateway_data_flows.json`
**What it is:** Onboarding use cases and data flow context  
**Use for:** Understanding initial workspace setup

---

### `gateway_personas_entitlements.json`
**What it is:** Engage/Unify feature entitlements  
**Use for:** Feature availability checks

---

### `gateway_summary.json`
**What it is:** High-level workspace summary  
**Includes:**
- Audit date
- Customer name, workspace slug/ID
- Counts: sources, destinations, audiences, journeys, spaces

---

## 📂 /for_gem_analysis/ - AI-Ready Format

### `workspace_audit_data.json`
**What it is:** Consolidated data formatted for Gemini Gem analysis  
**Structure:**
```json
{
  "workspace_summary": { ... },
  "sources": [ ... ],  // Includes FULL schemas
  "destinations": [ ... ],
  "audiences": [ ... ],
  "mtu_data": { ... },
  "audit_trail_summary": { ... },
  "profile_insights": [ ... ],
  "business_context": "Add context here before uploading"
}
```

**Use for:**
- Upload to **Segment SA Auditor Gem** for technical recommendations
- Upload to **Segment Use Case Builder Gem** for strategic use cases
- AI-powered analysis and insights

**Before uploading:**
1. Edit the `business_context` field
2. Add relevant customer information (industry, goals, pain points)
3. Upload to your Gem for analysis

---

## 📄 Documentation Files

### `README.txt`
Quick start guide with priority actions and recommended order

### `FILE_MANIFEST.txt`
Detailed file descriptions and use cases

---

## File Size Reference

Typical export for a medium workspace:
- Total: ~500KB - 2MB compressed
- gateway_sources.json: 50KB - 500KB (depends on event schema size)
- gateway_destinations.json: 20KB - 100KB
- workspace_audit_data.json: 100KB - 500KB

---

## What's Next?

### For Technical Audits:
1. Open `/processed/sources_with_destinations.csv`
2. Check for disabled sources or missing connections
3. Upload `/for_gem_analysis/workspace_audit_data.json` to SA Auditor Gem

### For Use Case Development:
1. Upload `/for_gem_analysis/workspace_audit_data.json` to Use Case Builder Gem
2. Review recommendations and prioritization
3. Share output with customer

### For Deep Dive Analysis:
1. Open `/raw_data/gateway_sources.json` in a JSON viewer
2. Analyze event schemas and properties
3. Cross-reference with audiences CSV for activation opportunities

---

## Schema Structure Deep Dive

The `gateway_sources.json` file contains the complete event schema for each source:

### Track Events:
```json
{
  "name": "track",
  "events": [
    {
      "name": "Order Completed",
      "description": "User completed purchase",
      "properties": {
        "order_id": {
          "type": "string",
          "description": "Unique order identifier"
        },
        "total": {
          "type": "number",
          "description": "Order total amount"
        }
      }
    }
  ]
}
```

### Identify Traits:
```json
{
  "name": "users",
  "objectProperties": [
    {
      "key": "email",
      "type": "string",
      "enabled": true,
      "archived": false
    },
    {
      "key": "plan_type",
      "type": "string",
      "enabled": true,
      "archived": false
    }
  ]
}
```

### Page/Screen Events:
```json
{
  "name": "page",
  "events": [
    {
      "name": "Product Detail Page",
      "properties": { ... }
    }
  ]
}
```

---

## Missing a File?

If a file is missing from your export:
- **gateway_sources.json is empty or has no schemas**: Run a new audit (schemas are fetched live)
- **MTU data is empty**: Workspace may not be on MTU plan or no usage data available
- **Some JSON files missing**: Feature may not be enabled for the workspace (e.g., Engage)

---

**Questions?** Check `GEMINI_GEMS_README.md` for Gem setup or `GEMINI_GEM_SETUP_GUIDE.md` for detailed instructions.
