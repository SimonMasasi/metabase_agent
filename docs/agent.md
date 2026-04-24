# Metabase Agent Endpoints (API v2)

Two endpoints provide AI-powered analysis and assistance for Metabase data exploration. The non-stream endpoint returns a complete response at once, while the stream endpoint provides real-time incremental responses for interactive experiences.

Base URL: `http://localhost:8000/api/v2/`

OpenAPI/Docs UI: `http://localhost:8000/api/v2/docs`

Auth: None by default (unless you've added middleware).

## Shared Request Schema

Content-Type: `application/json`

Body fields (MetabaseAgentRequest):
- `messages` (array, required): Chat-style conversation messages
  - `role` (string): "user", "assistant", or "system"
  - `content` (string): Message content
- `context` (object, required): User's current Metabase context
  - `user_is_viewing` (array, optional): Current charts/dashboards being viewed
    - `id` (number, optional): Question/dashboard ID
    - `type` (string): "question", "dashboard", etc.
    - `query` (object, optional): DatasetQuery details
    - `sql_engine` (string, optional): Database engine type
    - `chart_configs` (array, optional): Chart configuration details
    - `dashboard_image` (string, optional): Base64 dashboard screenshot
  - `current_user_time` (string, optional): ISO timestamp of user's current time
  - `capabilities` (array, optional): List of available features/permissions
- `state` (object, optional): Session state data (defaults to empty object)
- `user_id` (number, required): Unique user identifier
- `conversation_id` (string, required): Conversation thread identifier

Example file: `data/sample_agent_request.json` (available in this repo). Use directly with curl via `--data @data/sample_agent_request.json`.

---

## 1) Non-Stream Endpoint

- Method/Path: `POST /agent/non_stream`
- Purpose: Complete AI analysis response in a single JSON payload

Example curl:

```bash
curl -X POST \
  http://localhost:8000/api/v2/agent/non_stream \
  -H 'Content-Type: application/json' \
  --data @data/sample_agent_request.json
```

Successful response (200):
```json
{
  "messages": "<string with AI analysis and recommendations>",
  "state": {}
}
```

Error response:
```json
{
  "error": "Failed to generate answer",
  "details": "<error details>",
  "generated_answer": "Failed To generate answer"
}
```

---

## 2) Stream Endpoint

- Method/Path: `POST /agent/stream`
- Purpose: Real-time streaming AI responses for interactive chat experiences
- Content-Type (response): `text/event-stream`
- Stream format: Each event is a JSON object followed by a blank line (no `data:` prefix)

Recommended headers (client side): `Accept: text/event-stream`

Example curl (note `-N` to disable buffering):

```bash
curl -N -X POST \
  http://localhost:8000/api/v2/agent/stream \
  -H 'Content-Type: application/json' \
  -H 'Accept: text/event-stream' \
  --data @data/sample_agent_request.json
```

Typical stream events:
- Text chunk:
  ```json
  {"type": "text", "value": "partial response text..."}
  ```
- Tool usage notification:
  ```json
  {"toolCallId": "abc123", "toolName": "query_execution", "args": {"sql": "SELECT ..."}}
  ```
- Navigation instruction:
  ```json
  {"type": "navigate_to", "version": 1, "value": "/question/456"}
  ```
- Completion marker:
  ```json
  {"finishReason": "stop", "usage": {"promptTokens": 150, "completionTokens": 75}}
  ```

Error case: server emits JSON error message as part of the event stream.

### Minimal JavaScript client example

```javascript
const response = await fetch('http://localhost:8000/api/v2/agent/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream'
  },
  body: JSON.stringify(requestData)
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  buffer += decoder.decode(value, { stream: true });
  
  while (buffer.includes('\n\n')) {
    const [event, ...rest] = buffer.split('\n\n');
    buffer = rest.join('\n\n');
    
    if (event.trim()) {
      try {
        const data = JSON.parse(event.trim());
        console.log('Event:', data);
        // Handle different event types
        if (data.type === 'text') {
          // Display text chunk
        } else if (data.type === 'navigate_to') {
          // Handle navigation
        }
      } catch (e) {
        console.warn('Failed to parse event:', event);
      }
    }
  }
}
```

---

## Key Differences from Dashboard Agent

- **Context-aware**: Agent endpoints understand current Metabase viewing context (charts, dashboards, queries)
- **Interactive**: Designed for back-and-forth conversation with state management
- **Tool integration**: Can execute queries, create charts, and navigate within Metabase
- **User-specific**: Requires `user_id` and respects user capabilities/permissions

## When to use each endpoint

- Use `/non_stream` for batch analysis, reporting, or when you need the complete response before proceeding
- Use `/stream` for interactive chat experiences, live dashboards, or when building conversational interfaces

## Context Tips

- Include current dashboard/chart IDs in `user_is_viewing` for context-aware responses
- Set `current_user_time` for time-sensitive analysis
- Populate `capabilities` to respect user permissions
- Use meaningful `conversation_id` values to maintain conversation history

## Troubleshooting

- 400/422: Ensure required fields (`messages`, `context`, `user_id`, `conversation_id`) are present
- Missing context: Agent works better with rich context about what the user is currently viewing
- Stream buffering: Use appropriate HTTP client settings to handle real-time streaming
- CORS/Auth: Configure your client for any authentication middleware you've added