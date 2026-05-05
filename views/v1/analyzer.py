from django.http import HttpRequest
from ninja import Router

from serializers.baseSerializer import ResultsSchema
from utils.image_ai_completion import get_analysis_from_image
from utils.logging import metabase_helpers_logging
import json

analyzer_router = Router()

logging = metabase_helpers_logging()


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


@analyzer_router.get("/tokes_status")
def get_token_feature(request: HttpRequest):
    try:

        logging.info("successfully fetched token features")

        return {
                "valid": True,
                "status": "OK",
                "error-details": None,
                "canonical?": True,
                "features": ["sandboxes", "audit-app"],
                "plan-alias": "pro",
                "trial": False,
                "valid-thru": "2026-12-31",
                "max-users": 100,
                "company": "Acme Corp",
                "store-users": [
                    { "email": "simonejohnee@gmail.com" },
                    { "email": "simonejohnee@gmail.com" }
                ],
                "meters": {
                    "api-calls": 5000,
                    "storage-gb": 50
                },
                "quotas": [
                    { "name": "users", "limit": 100, "used": 45 }
                ]
            }

    except Exception as e:
        logging.error(f"error occurred {e}")
        return {
            "valid": False,
            "status": "error",
            "error-details": str(e),
            "features": None,
            "plan-alias": None,
            "trial": None,
            "valid-thru": None,
            "max-users": None,
            "company": None,
        }
