import json
from uuid import uuid4

from django.http import StreamingHttpResponse
from ninja import Router

from agents.py_dantic_agent import analytics_steaming_agent
from constants.metabase_request_schemas import MetabaseAgentRequest
from utils.logging import metabase_agent_logging

logging = metabase_agent_logging()


anthropic_router = Router()


def _anthropic_sse_event(event_name, payload):
    return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"


async def _to_anthropic_sse_frames(stream, model_name):
    """Translate the app's internal stream protocol into Anthropic-style SSE events."""
    message_id = f"msg_{uuid4().hex}"
    stop_sent = False
    content_open = False

    yield _anthropic_sse_event(
        "message_start",
        {
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": model_name,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        },
    )

    async for chunk in stream:
        if chunk is None:
            continue

        text = str(chunk).strip()
        if not text or ":" not in text:
            continue

        prefix, payload_text = text.split(":", 1)

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            logging.warning("Skipping non-JSON stream payload: %s", text)
            continue

        if prefix == "0" and payload.get("type") == "text":
            if not content_open:
                yield _anthropic_sse_event(
                    "content_block_start",
                    {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {"type": "text", "text": ""},
                    },
                )
                content_open = True

            yield _anthropic_sse_event(
                "content_block_delta",
                {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {
                        "type": "text_delta",
                        "text": payload.get("value", ""),
                    },
                },
            )
            continue

        if prefix == "d":
            if not content_open:
                yield _anthropic_sse_event(
                    "content_block_start",
                    {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {"type": "text", "text": ""},
                    },
                )
                content_open = True

            yield _anthropic_sse_event(
                "content_block_stop",
                {"type": "content_block_stop", "index": 0},
            )
            yield _anthropic_sse_event(
                "message_delta",
                {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": 0},
                },
            )
            yield _anthropic_sse_event("message_stop", {"type": "message_stop"})
            stop_sent = True
            break

    if not stop_sent:
        if not content_open:
            yield _anthropic_sse_event(
                "content_block_start",
                {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""},
                },
            )

        yield _anthropic_sse_event(
            "content_block_stop",
            {"type": "content_block_stop", "index": 0},
        )
        yield _anthropic_sse_event(
            "message_delta",
            {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": 0},
            },
        )
        yield _anthropic_sse_event("message_stop", {"type": "message_stop"})


@anthropic_router.get("/v1/models")
def get_models(request):
    return {
        "data": [
            {
                "id": "anthropic/claude-3-haiku",
                "display_name": "Claude 3 Haiku",
                "name": "claude-3-haiku",
                "created": 1712361600,
            },
            {
                "id": "openai/gpt-4o",
                "display_name": "GPT-4o",
                "name": "gpt-4o",
                "created": 1715299200,
            },
        ]
    }


@anthropic_router.post("/v1/messages")
def get_messages(request, input_data: MetabaseAgentRequest):
    try:

        return StreamingHttpResponse(
            _to_anthropic_sse_frames(
                analytics_steaming_agent(input_data),
                model_name=input_data.model,
            ),
            content_type="text/event-stream",
        )
    except Exception as e:
        logging.error(f"Unexpected Error Occured: {str(e)}")

        async def error_stream():
            yield _anthropic_sse_event(
                "message_start",
                {
                    "type": "message_start",
                    "message": {
                        "id": f"msg_{uuid4().hex}",
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": input_data.model,
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 0, "output_tokens": 0},
                    },
                },
            )
            yield _anthropic_sse_event(
                "content_block_start",
                {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""},
                },
            )
            yield _anthropic_sse_event(
                "content_block_delta",
                {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {
                        "type": "text_delta",
                        "text": f"Failed to get data {str(e)}",
                    },
                },
            )
            yield _anthropic_sse_event(
                "content_block_stop",
                {"type": "content_block_stop", "index": 0},
            )
            yield _anthropic_sse_event(
                "message_delta",
                {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": 0},
                },
            )
            yield _anthropic_sse_event("message_stop", {"type": "message_stop"})

        return StreamingHttpResponse(
            streaming_content=error_stream(),
            content_type="text/event-stream",
        )
