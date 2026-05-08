from django.http import HttpRequest
from ninja import Router

from serializers.baseSerializer import ResultsSchema
from utils.image_ai_completion import get_analysis_from_image
from utils.logging import metabase_agent_logging
import json

analyzer_router = Router()

logging = metabase_agent_logging()


@analyzer_router.post("/chart", response=ResultsSchema)
def analyze_chart(request: HttpRequest):

    try:
        """
        Analyze a chart based on the provided request data.
        """

        json_data = json.loads(request.body.decode("utf-8"))

        base_64_image = json_data.get("image_base64", None)

        if not base_64_image:
            return {
                "error": "No base64_image provided in the request",
                "analysis": "Base64 image is required for analysis.",
            }

        analysis = get_analysis_from_image(
            "Analyze this dashboard", base64_image=base_64_image, model="gpt-4.1"
        )

        # Placeholder for chart analysis logic
        return {"analysis": analysis, "error": None}
    except Exception as e:
        logging.error(f"Error analyzing chart: {str(e)}")
        return {
            "error": "Failed to analyze chart",
            "details": str(e),
            "analysis": "Failed To Perform Analysis",
        }


@analyzer_router.post("/dashboard", response=ResultsSchema)
def analyze_dashboard(request: HttpRequest):
    """
    Analyze a dashboard based on the provided request data.
    """
    try:
        json_data = json.loads(request.body.decode("utf-8"))

        base_64_image = json_data.get("image_base64", None)

        if not base_64_image:
            return {
                "error": "No base64_image provided in the request",
                "analysis": "Base64 image is required for analysis.",
            }

        analysis = get_analysis_from_image(
            "Analyze this dashboard", base64_image=base_64_image, model="gpt-4.1"
        )

        # Placeholder for dashboard analysis logic
        return {"analysis": analysis, "error": None}

    except Exception as e:
        logging.error(f"Error analyzing dashboard: {str(e)}")
        return {
            "error": "Failed to analyze dashboard",
            "details": str(e),
            "analysis": "Failed To Perform Analysis",
        }
