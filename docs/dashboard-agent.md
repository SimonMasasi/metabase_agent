# Dashboard Agent Endpoints (API v2)

Two endpoints let you analyze dashboard data with the agent. Use the non-stream endpoint for a single JSON response, or the stream endpoint to receive incremental output suitable for live UIs.

Base URL: `http://localhost:8000/api/v2/`

OpenAPI/Docs UI: `http://localhost:8000/api/v2/docs`

Auth: None by default (unless you’ve added middleware). Use standard headers below.

## Shared Request Schema

Content-Type: `application/json`

Body fields:
- `message` (string, optional): Instruction for the agent. If omitted, defaults to "Analyze the dashboard data and provide insights." 
- `dashboard_data` (array, required): List of dashboard blocks.
  - `name` (string, required): Block name.
  - `data` (object, required): Arbitrary JSON your dashboard provides.
- `conversation_id` (string, required): Conversation key to thread history across requests.

Example file: `data/sample_dashboard_request.json` (added in this repo). You can use it directly with curl via `--data @data/sample_dashboard_request.json`.

---

## 1) Non-Stream Endpoint

- Method/Path: `POST /dashboard_analysis/non_stream`
- Purpose: Single-shot analysis; returns one consolidated JSON response.

Example curl:

```bash
curl -X POST \
  http://localhost:8000/api/v2/dashboard_analysis/non_stream \
  -H 'Content-Type: application/json' \
  --data @data/sample_dashboard_request.json
```

Successful response (200):
```json
{
  "success": true,
  "message": "Answer generated successfully",
  "data": "<string with the agent’s final analysis>"
}
```

Error response:
```json
{
  "success": false,
  "message": "Failed to generate answer",
  "data": "Failed To generate answer: <error>"
}
```

---

## 2) Stream Endpoint

- Method/Path: `POST /dashboard_analysis/stream`
- Purpose: Server-sent style streaming analysis for live UIs.
- Content-Type (response): `text/event-stream`
- Stream format: Each message is a standalone JSON object followed by a blank line. There is no `data:` prefix; split on double newlines to parse events.

Recommended headers (client side): `Accept: text/event-stream`

Example curl (note `-N` to disable buffering):

```bash
curl -N -X POST \
  http://localhost:8000/api/v2/dashboard_analysis/stream \
  -H 'Content-Type: application/json' \
  -H 'Accept: text/event-stream' \
  --data @data/sample_dashboard_request.json
```

Typical stream events you may receive:
- Text token chunk:
  ```json
  {"type": "text", "value": "partial text ..."}
  ```
- Tool call notification:
  ```json
  {"toolCallId": "abc123", "toolName": "some_tool", "args": {"k": "v"}}
  ```
- Navigation instruction (e.g., to a chart):
  ```json
  {"type": "navigate_to", "version": 1, "value": "/question/123"}
  ```
- Completion marker:
  ```json
  {"finishReason": "stop", "usage": {"promptTokens": 0, "completionTokens": 0}}
  ```

Error case (stream): server emits a JSON text message indicating failure, still as part of the event stream.

### Minimal Python consumer example

```python
import requests

url = "http://localhost:8000/api/v2/dashboard_analysis/stream"
headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
with open("data/sample_dashboard_request.json", "rb") as f:
    with requests.post(url, headers=headers, data=f, stream=True) as r:
        buf = b""
        for chunk in r.iter_content(chunk_size=None):
            if not chunk:
                continue
            buf += chunk
            while b"\n\n" in buf:
                line, buf = buf.split(b"\n\n", 1)
                line = line.strip()
                if line:
                    print("EVENT:", line.decode("utf-8"))
```

---

## When to use each endpoint
- Use `/non_stream` when you want a single, final answer per request.
- Use `/stream` when building a live UI that renders incremental output, tool activity, and navigation hints.

## Notes on conversation history
- Both endpoints read and write message history keyed by `conversation_id` so the agent can maintain context across requests.

## Troubleshooting
- 400/422: Ensure `dashboard_data` is an array of objects each with `name` and `data` (object), and include `conversation_id`.
- Streaming stalls: Verify server logs and use `curl -N` or an HTTP client that doesn’t buffer.
- CORS/CSRF: If you add auth or CSRF, configure your client accordingly.
