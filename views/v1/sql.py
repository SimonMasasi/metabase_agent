from django.http import HttpRequest
from ninja import Router

from agents.sql_generation import generate_sql_from_request
from agents.sql_fix import fix_sql_query
from utils.logging import metabase_helpers_logging
import json

logging = metabase_helpers_logging()


sql_router = Router()


@sql_router.post("/generate")
def generate_sql(request: HttpRequest):
    try:
        """
        Generate SQL queries based on the provided request data.
        """

        sql_data = json.loads(request.body.decode("utf-8"))

        logging.info("received request with sql_data")
        logging.info(sql_data)

        if not sql_data:
            return {
                "error": "No request is provided in the request",
                "generated_sql": " is required for analysis.",
            }

        generation = generate_sql_from_request(request=sql_data)

        logging.info("generated sql")
        logging.info(generation)

        # Placeholder for chart analysis logic
        return {"generated_sql": generation, "error": None}
    except Exception as e:
        logging.error(f"Error analyzing chart: {str(e)}")
        return {
            "error": "Failed to generate sql",
            "details": str(e),
            "generated_sql": "Failed To generate sql",
        }


@sql_router.post("/fix")
def fix_sql(request: HttpRequest):
    try:
        """
        Fix SQL queries based on the provided request data.
        """

        sql_data = json.loads(request.body.decode("utf-8"))

        logging.info("received request with sql_data")
        logging.info(sql_data)

        if not sql_data:
            return {"error": "No request is provided in the request", "fixes": []}

        generation = fix_sql_query(request=sql_data)

        logging.info("corrected_sql")
        logging.info(generation)

        return {"fixes": [{"fixed_sql": generation, "line_number": 1}], "error": None}

    except Exception as e:
        logging.error(f"Error fixing SQL: {str(e)}")
        return {"error": "Failed to fix sql", "details": str(e), "fixes": []}
