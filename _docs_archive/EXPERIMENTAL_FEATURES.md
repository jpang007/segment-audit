# Experimental Features

## Recommendations Tab (AI-Powered Analysis)

The Recommendations tab provides AI-powered workspace analysis using Google's Gemini API. This feature is **experimental** and can be toggled on/off.

### Status
- ✅ **Local Development**: Enabled by default
- ❌ **Production (Render)**: Disabled by default

### How to Enable/Disable

#### Local Development
1. Create or edit `.env` file in project root
2. Add: `ENABLE_EXPERIMENTAL_FEATURES=true`
3. Restart Flask app

```bash
# .env file
GEMINI_API_KEY=your_api_key_here
ENABLE_EXPERIMENTAL_FEATURES=true
```

#### Production (Render)
1. Go to Render dashboard → Environment
2. Add environment variable:
   - **Key**: `ENABLE_EXPERIMENTAL_FEATURES`
   - **Value**: `true`
3. Redeploy

To disable in production, simply remove the environment variable or set to `false`.

### What Gets Hidden When Disabled

When `ENABLE_EXPERIMENTAL_FEATURES=false` (or not set):
- 💡 Recommendations link removed from navigation
- `/recommendations` route returns 404
- `/api/generate-recommendations` API returns 404

All other features (Sources, Audiences, Destinations, Journeys, Profile Insights) remain fully functional.

### Why This Exists

The Recommendations tab is still in development and uses:
- Gemini API (rate limits, costs, experimental prompts)
- Complex AI analysis (may produce incorrect results)
- New schema health detection (needs testing)
- Business context inference (automotive/marketplace detection)

By gating it behind a feature flag, we can:
- ✅ Test freely in local development
- ✅ Keep production stable
- ✅ Enable for specific customers when ready
- ✅ Roll out gradually

### Current Capabilities

When enabled, the Recommendations tab provides:

1. **Workspace Audit**
   - Schema health (event explosion detection)
   - Source health analysis
   - Audience activation gaps
   - Profile insights integration
   - Journey maturity assessment

2. **Activation & Expansion**
   - Unused audiences with user counts
   - Unused destinations
   - Missing activation flows
   - Segment product opportunities

3. **Growth Use Cases**
   - Evidence-based recommendations
   - Business context awareness
   - Industry-specific suggestions

### Testing Notes

Before enabling in production:
- [ ] Run audit on 3-5 diverse workspaces
- [ ] Verify automotive/marketplace detection works
- [ ] Confirm schema health flags 4k+ event sources as P0
- [ ] Test with rate-limited Gemini API
- [ ] Validate all visual renderers display correctly
- [ ] Check mobile responsiveness

### Troubleshooting

**"Feature not available" message**
- Check `.env` file has `ENABLE_EXPERIMENTAL_FEATURES=true`
- Restart Flask app after changing `.env`
- In production, check Render environment variables

**Gemini API errors**
- Rate limited: Wait 60 seconds
- 404 model errors: Check model name in `app.py` line ~2922
- Timeout: Increase timeout in `gemini_client.py` (currently 180s)

**No event counts in schema health**
- Run fresh audit collection (not just generate recommendations)
- Check `audit_data/gateway_sources.csv` has "Event Count" column
- If missing, audit ran before code changes - re-run audit

---

Last updated: 2026-05-07
