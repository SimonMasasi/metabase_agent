import json

from django.http import StreamingHttpResponse
from ninja import Router

from agents.anthropic_agent import anthropic_streaming_agent_runner
from constants.metabase_request_schemas import MetabaseAgentRequest
from utils.logging import metabase_agent_logging

logging = metabase_agent_logging()


anthropic_router = Router()


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

    #save the input_data in the folder /data in the file new_json.json for debugging purposes
    with open("data/new_json.json", "w") as f:
        json.dump(input_data.model_dump(), f, indent=4)

    return StreamingHttpResponse(
        streaming_content=anthropic_streaming_agent_runner(input_data),
        content_type="text/event-stream",
    )
