from django.http import HttpRequest
from ninja import Router

from constants.metabase_request_schemas import MetabaseAgentRequest
from utils.logging import metabase_helpers_logging
import json
from agents.ask import get_metabot_response
from django.http import StreamingHttpResponse

from agents.py_dantic_agent import analytics_steaming_agent

logging = metabase_helpers_logging()


agent_router = Router()


@agent_router.post("/non_stream")
def non_stream_agent(request: HttpRequest):
    """AI-powered Metabase analysis with complete response in single JSON payload.

    Route: POST /api/v2/agent/non_stream
    Body: Raw JSON with MetabaseAgentRequest structure:
      { messages: [{role, content}], context: UserContext, user_id: int, conversation_id: str }
    Returns: { messages: str, state: {} } on success or { error, details, generated_answer } on failure
    See `docs/agent.md` for full schema details and examples.
    """
    try:

        agent_data = json.loads(request.body.decode("utf-8"))


        answer = get_metabot_response(metabase_request=agent_data)

        logging.info("generated_answer")

        # Placeholder for chart analysis logic
        return {"messages": answer, "state": {}}
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {
            "error": "Failed to generate answer",
            "details": str(e),
            "generated_answer": "Failed To generate answer",
        }


@agent_router.post("/stream")
async def stream_agent(request: HttpRequest, input_data: MetabaseAgentRequest):
    """AI-powered Metabase analysis with real-time streaming responses.

    Route: POST /api/v2/agent/stream
    Body: MetabaseAgentRequest { messages: [{role, content}], context: UserContext, user_id: int, conversation_id: str }
    Response: text/event-stream with JSON events separated by blank lines
    Events include text chunks, tool calls, navigation hints, and completion markers
    See `docs/agent.md` for streaming client examples and event formats.
    """
    try:

        if input_data.messages is None or input_data.context is None:
            raise ValueError("Request must contain a 'message' field")

        return StreamingHttpResponse(
            analytics_steaming_agent(input_data),
            content_type="text/event-stream",
        )
    except Exception as e:
        logging.error(f"Unexpected Error Occured: {str(e)}")
        return StreamingHttpResponse(
            streaming_content=(
                f"0:{{'value': f'Failed to get data {str(e)} ', 'type': 'text'}}\n\n"
            ),
            content_type="text/event-stream",
        )
