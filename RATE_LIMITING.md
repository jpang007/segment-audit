# Rate Limiting Protection

## What Changed

Added automatic rate limiting to prevent Gateway API errors during audits.

## Protections Added

### 1. Base Request Throttling
- **Minimum 1 second** between all Gateway API requests
- Automatic tracking of last request time
- Sleep delays inserted automatically before each request

### 2. Retry Logic with Exponential Backoff
If rate limited (HTTP 429 or GraphQL rate limit error):
- **Attempt 1**: Wait 5 seconds, retry
- **Attempt 2**: Wait 10 seconds, retry
- **Attempt 3**: Wait 20 seconds, retry
- After 3 attempts: Show clear error message

### 3. Additional Collection Delays
- **Audiences**: 0.5s delay between each space query
- **Journeys**: 0.5s delay between each space query
- **Audit Trail**: 0.3s delay between pagination pages
- **Audience Definitions**: 2s delay between each definition fetch

### 4. Error Detection
Catches rate limits in two forms:
- HTTP 429 status codes
- GraphQL errors containing "rate limit" message

## User Experience

- Landing page shows rate limiting info box
- Audits take 2-5 minutes depending on workspace size
- Progress bar updates throughout
- Clear error messages if limits still exceeded

## Technical Details

```python
# In GatewayAPIClient.__init__
self.last_request_time = 0
self.min_request_interval = 1.0  # 1 second

# In _execute_query
current_time = time.time()
time_since_last_request = current_time - self.last_request_time
if time_since_last_request < self.min_request_interval:
    sleep_time = self.min_request_interval - time_since_last_request
    time.sleep(sleep_time)
```

## Files Modified

1. `/Users/jpang/segment-audit-dashboard/app.py`
   - Added rate limiting to `GatewayAPIClient`
   - Added delays in audit collection loops
   - Enhanced retry logic for rate limit errors

2. `/Users/jpang/segment-audit-dashboard/templates/gateway_index.html`
   - Added rate limiting info box on landing page

## Testing

To test rate limiting:
1. Run audit with all options checked
2. Monitor console logs for rate limit messages
3. Verify automatic retries happen
4. Confirm audit completes successfully

## Future Improvements

If rate limits still occur:
- Increase `min_request_interval` to 1.5s or 2s
- Add more delays between batch operations
- Implement exponential backoff for all requests
