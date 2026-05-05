from django.http import HttpRequest
from ninja import Router

from serializers.baseSerializer import ResultsSchema
from utils.logging import metabase_helpers_logging

license_router = Router()

logging = metabase_helpers_logging()


@license_router.get("/{token}/v2/status")
def get_license_status(request: HttpRequest, token: str):
    """
    Get license/token status for a given token.
    Accepts query parameters: site-uuid, mb-version
    """
    try:
        site_uuid = request.GET.get("site-uuid")
        mb_version = request.GET.get("mb-version")

        logging.info(
            f"Fetched license status for token: {token}, site-uuid: {site_uuid}, mb-version: {mb_version}"
        )

        return {
            "valid": True,
            "status": "OK",
            "error-details": None,
            "canonical?": True,
            "features": [
                "attached_dwh",
                "advanced_permissions",
                "audit_app",
                "cache_granular_controls",
                "cloud_custom_smtp",
                "content_translation",
                "content_verification",
                "disable_password_login",
                "embedding",
                "embedding_sdk",
                "embedding_simple",
                "hosting",
                "offer-metabase-ai-managed",
                "metabase-ai-managed",
                "metabot-v3",
                "official_collections",
                "sandboxes",
                "scim",
                "sso_google",
                "sso_jwt",
                "sso_ldap",
                "sso_oidc",
                "sso_saml",
                "sso_slack",
                "session_timeout_config",
                "whitelabel",
                "serialization",
                "dashboard_subscription_filters",
                "snippet_collections",
                "email_allow_list",
                "email_restrict_recipients",
                "upload_management",
                "collection_cleanup",
                "cache_preemptive",
                "ai_sql_fixer",
                "ai_sql_generation",
                "ai_entity_analysis",
                "database_routing",
                "development_mode",
                "etl_connections",
                "etl_connections_pg",
                "table_data_editing",
                "remote_sync",
                "dependencies",
                "semantic_search",
                "transforms-python",
                "transforms-basic",
                "library",
                "support-users",
                "tenants",
                "writable_connection",
                "admin_security_center",
                "ai_controls",
            ],
            "plan-alias": "pro-self-hosted",
            "trial": False,
            "valid-thru": "2026-12-31",
            "max-users": 100,
            "company": "Masasi Corp",
            "store-users": [
                {"email": "simonejohnee@gmail.com"},
                {"email": "simonejohnee@gmail.com"},
            ],
            "meters": {"api-calls": 5000, "storage-gb": 50},
            "quotas": [{"name": "users", "limit": 100, "used": 45}],
        }
    except Exception as e:
        logging.error(f"Error fetching license status: {str(e)}")
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


@license_router.post("/{token}/v2/metering")
def report_metering(request: HttpRequest, token: str):
    """
    Report metering data for a given token.
    Accepts JSON body with metering data.
    """
    try:
        logging.info(f"Received metering data for token: {token}")

        # Placeholder for processing metering data logic
        return {"status": 200, "data":{}}

    except Exception as e:
        logging.error(f"Error reporting metering data: {str(e)}")
        return {
            "status":500,
            "error-details": str(e),
        }