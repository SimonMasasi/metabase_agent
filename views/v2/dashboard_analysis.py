from django.http import HttpRequest
from ninja import Router

from constants.metabase_request_schemas import DashboardAnalysisRequest , DashboardDataResponse
from utils.logging import metabase_helpers_logging
import json
from django.http import StreamingHttpResponse

from agents.dashboard_agent import dashboard_steaming_agent , dashboard_agent_non_stream

logging = metabase_helpers_logging()


dashboard_analysis_router = Router()


@dashboard_analysis_router.post("/non_stream" , response=DashboardDataResponse)
async def non_stream_dashboard_agent(request: HttpRequest , input_data: DashboardAnalysisRequest):
    """Analyze dashboard data and return a single JSON response.

    Route: POST /api/v2/dashboard_analysis/non_stream
    Body: DashboardAnalysisRequest { message?: str, dashboard_data: [{name, data}], conversation_id: str }
    Returns: DashboardDataResponse { success: bool, message?: str, data?: str }
    See `docs/dashboard-agent.md` for examples.
    """
    try:

        logging.info(str(request.body))
        logging.info(str(request.headers))


        logging.info("received request with agent_data")
        logging.info(input_data)

        answer = await dashboard_agent_non_stream(user_data=input_data)

        logging.info("generated_answer")
        logging.info(answer)

        # Placeholder for chart analysis logic
        return DashboardDataResponse(success=True, message="Answer generated successfully", data=answer)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return DashboardDataResponse(
            success=False,
            message="Failed to generate answer",
            data=f"Failed To generate answer: {str(e)}",
        )


@dashboard_analysis_router.post("/stream")
async def stream_dashboard_agent(request: HttpRequest, input_data: DashboardAnalysisRequest):
    """Analyze dashboard data and stream incremental JSON events.

    Route: POST /api/v2/dashboard_analysis/stream
    Body: DashboardAnalysisRequest { message?: str, dashboard_data: [{name, data}], conversation_id: str }
    Response: text/event-stream; events are JSON objects separated by blank lines.
    See `docs/dashboard-agent.md` for examples and a minimal client.
    """
    try:


        return StreamingHttpResponse(
            dashboard_steaming_agent(input_data),
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
