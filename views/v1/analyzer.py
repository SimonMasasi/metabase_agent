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
            "status": "active",
            "error-details": None,
            "features": [
                "advanced-config",
                "advanced-permissions",
                "audit-app",
                "cache-granular-controls",
                "collection-cleanup",
                "config-text-file",
                "content-management",
                "content-verification",
                "dashboard-subscription-filters",
                "database-auth-providers",
                "disable-password-login",
                "email-allow-list",
                "email-restrict-recipients",
                "embedding-sdk",
                "embedding",
                "hosting",
                "metabase-store-managed",
                "metabot-v3",
                "no-upsell",
                "official-collections",
                "query-reference-validation",
                "question-error-logs",
                "sandboxes",
                "scim",
                "serialization",
                "session-timeout-config",
                "snippet-collections",
                "sso-google",
                "sso-jwt",
                "sso-ldap",
                "sso-saml",
                "sso",
                "upload-management",
                "whitelabel",
            ],
            "plan-alias": "pro-self-hosted",
            "trial": False,
            "valid-thru": "2099-12-31T12:00:00",
            "max-users": 100,
            "company": "ega",
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
