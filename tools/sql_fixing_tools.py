from typing import Dict, Any
from pydantic_ai import RunContext
import base64
import json
from constants.metabase_request_schemas import MetabaseAgentRequest
from utils.logging import metabase_agent_logging
from utils.metabase_api import MetabaseAPIService


logging = metabase_agent_logging()
metabase_api = MetabaseAPIService()


async def get_quey_data_to_fix_from_sql_error(
    ctx: RunContext[MetabaseAgentRequest],
) -> Dict[str, Any]:

    try:
        viewing_contexts = ctx.deps.context.user_is_viewing
        if not viewing_contexts:
            logging.info("No viewing context available.")
            return {"error": "No viewing context available."}

        sql_fixing_content = []
        for viewing_content in viewing_contexts:

            if viewing_content.type != "adhoc":
                logging.info(
                    f"Skipping non-adhoc content with id {viewing_content.id} and type {viewing_content.type}."
                )
                continue

            sql_fixing_content.append(
                {
                    "id": viewing_content.id,
                    "type": viewing_content.type,
                    "error": viewing_content.error,
                    "sql_engine": viewing_content.sql_engine,
                    "query": (
                        viewing_content.query.model_dump()
                        if viewing_content.query
                        else None
                    ),
                    "chart_configs": [
                        {
                            "display_type": chart_config.display_type,
                            "query": (
                                chart_config.query.model_dump()
                                if chart_config.query
                                else None
                            ),
                            "native": (
                                chart_config.native.model_dump()
                                if chart_config.native
                                else None
                            ),
                        }
                        for chart_config in viewing_content.chart_configs
                    ],
                }
            )

        return {"sql_fixing_content": sql_fixing_content}

    except Exception as e:
        logging.error(f"Error in get_quey_data_to_fix_from_sql_error: {str(e)}")
        return {"error": str(e)}


async def display_fixed_sql_in_editor(
    ctx: RunContext[MetabaseAgentRequest], corrected_sql: str
) ->str:

    try:

        user_is_currently_viewing = ctx.deps.context.user_is_viewing

        if len(user_is_currently_viewing) == 0:
            logging.info("no user content currently viewing Found")
            return "No user content currently viewing Found"

        user_is_currently_viewing_data = user_is_currently_viewing[0]

        query = user_is_currently_viewing_data.query

        if query is None:
            return "No query found for the current viewing context"

        database = query.database
        type_of_query = "native"
        display_type = "table"
        template_args = {}
        parameters = []
        visualization_settings = {}
        question_type = "question"

        ## TODO use the users request to resolve all of the above attributes

        json_data = {
            "dataset_query": {
                "database": database,
                "type": type_of_query,
                "native": {"template-tags": template_args, "query": corrected_sql},
            },
            "display": display_type,
            "parameters": parameters,
            "visualization_settings": visualization_settings,
            "type": question_type,
        }

        base_64_context = base64.b64encode(json.dumps(json_data).encode()).decode()

        return "sql_fixed#" + base_64_context

    except Exception as e:
        logging.error(f"Error Occurred while displaying sql in editor: {str(e)}")
        return "Error Occurred while displaying sql in editor"