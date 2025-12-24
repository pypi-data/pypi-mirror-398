# Changelog - Client Update for New Server API v1.0

## Summary of Changes

This update rebuilds the glucosedao_client to work with the new GluRPC server API version 1.0. Key improvements include proper request cancellation, comprehensive health monitoring, and full API compatibility.

## 🎯 Key Features

### 1. Request Cancellation (Reduces Server Load)

**Problem:** When users move the slider quickly, multiple plot requests would pile up on the server, wasting resources.

**Solution:** Multi-level cancellation strategy:
- **Client-side tracking:** Tracks request IDs to avoid making unnecessary requests
- **Server-side cancellation:** Server automatically cancels previous incomplete requests for the same (handle, index)
- **Handle validation:** Discards responses if the file was changed/unloaded during the request

**Cancellation scenarios:**
1. **Slider moves quickly:** User slides from position 10 → 20 → 30
   - Requests for 10 and 20 are cancelled, only 30 completes
2. **File changed:** User uploads file A, starts plotting, then uploads file B
   - Old requests for file A are discarded
3. **File cleared:** User clears the file upload while plotting
   - Pending requests are ignored

### 2. Comprehensive Health Monitoring

**Static Metrics (Counters that only increase):**
- Total HTTP requests
- Total HTTP errors  
- Total calculation runs
- Total calculation errors
- Total inference errors
- Cache size
- Models initialized status
- Device information
- Queue capacities

**Dynamic Metrics (Real-time graphs, 60-second sliding window):**
- Request times (avg, median, min, max)
- Memory usage (MB)
- Model fulfillment time (ms)
- Queue sizes (inference & calc)

**Features:**
- Automatic polling every 1 second
- Historical graphs showing trends
- Load status indicator (idle → lightly loaded → heavily loaded → overloaded → full)

### 3. API Compatibility Updates

**Updated Data Models:**
- `HealthResponse`: Added 15+ new fields matching server API v1.0
- `QuickPlotResponse`: Removed incorrect `handle` field
- Added `force_calculate` parameter to all processing endpoints

**New Status Codes Handled:**
- `499 Client Closed Request`: Server detected client disconnect
- `503 Service Unavailable`: Server overloaded
- `504 Gateway Timeout`: Request took too long

**Index Handling:**
- Server uses negative indexing (0 = most recent, -1 = second-to-last, etc.)
- Client slider uses positive indexing (0 = first, N-1 = last)
- Automatic conversion between the two

## 📝 Detailed Changes

### client.py

**HealthResponse dataclass:**
```python
# Added fields:
- load_status: str
- priority_queue_length: int
- general_queue_length: int
- avg_request_time_ms, median_request_time_ms, min_request_time_ms, max_request_time_ms: float
- inference_requests_by_priority: Dict[str, int]
- total_inference_errors, total_calc_runs, total_calc_errors: int
- inference_queue_size, inference_queue_capacity: int
- calc_queue_size, calc_queue_capacity: int
```

**draw_plot() method:**
- Added `force_calculate` parameter
- Added handling for 499 status code (client disconnect)
- Better error logging with status codes

**quick_plot() method:**
- Added `force_calculate` parameter
- Removed incorrect `handle` field from response

### app.py

**Health monitoring:**
- `health_history` and `health_timestamps`: 60-second sliding window of metrics
- `check_server_health()`: Returns both static HTML and dynamic Plotly graph
- `create_health_metrics_graph()`: 3-row subplot with request times, memory/fulfillment, and queue sizes
- `poll_health()`: Called every 1 second by Gradio timer

**Request cancellation:**
- `request_counter` and `pending_request_id`: Track the latest request
- `predict_glucose()`: Captures handle at start, validates before and after network call
- Discards responses if file changed or newer request arrived

**UI improvements:**
- Health monitor in expandable accordion (open by default)
- Manual health check button
- Real-time updates with no manual refresh needed
- Improved error messages and status indicators

## 🔧 Usage Examples

### Slider Cancellation
```python
# User drags slider: 0 → 50 → 100
# Only the request for index 100 completes
# Requests for 0 and 50 are cancelled client-side
# Server also cancels any in-flight requests for the same handle
```

### File Change Handling
```python
# 1. User uploads file A, handle="abc123"
# 2. Starts plotting index 50
# 3. User uploads file B, handle="xyz789" 
# 4. Request for file A completes but is discarded
# 5. Only plots from file B are shown
```

### Health Polling
```python
# Timer ticks every 1 second
# Fetches latest health metrics
# Updates graphs with new data point
# Maintains 60-second sliding window
```

## 🧪 Testing

Run basic tests:
```bash
uv run python test_setup.py
```

All tests pass:
- ✅ Imports
- ✅ Client creation
- ✅ Gradio app creation
- ✅ Server utilities

## 📚 Documentation Updates

- `example.py`: Updated to use Plotly JSON responses instead of PNG bytes
- `API_REFERENCE.md`: Already up to date with server v1.0
- `README.md`: Will need updates to document new features

## 🚀 Next Steps

1. Test with real server to verify cancellation behavior
2. Update README.md with new health monitoring features
3. Add screenshots of new health monitor UI
4. Consider adding configurable polling interval

## ⚠️ Breaking Changes

**For existing users:**
- `draw_plot()` now returns Plotly JSON dict instead of PNG bytes
- Must save plots as HTML using `fig.write_html()` instead of writing PNG bytes
- `QuickPlotResponse` no longer has `handle` field
- Health response structure completely changed

**Migration guide:**
```python
# Old code:
png_bytes = client.draw_plot(handle, index)
with open("plot.png", "wb") as f:
    f.write(png_bytes)

# New code:
plot_data = client.draw_plot(handle, index)
fig = go.Figure(plot_data)
fig.write_html("plot.html")
# Or display in Gradio: gr.Plot(value=fig)
```

## 🎉 Benefits

1. **Reduced server load:** Cancelled requests free up server resources
2. **Better user experience:** No stale plots, faster response times
3. **Real-time monitoring:** See server health at a glance
4. **Production ready:** Proper error handling and status codes
5. **API v1.0 compatible:** Works with latest server features
