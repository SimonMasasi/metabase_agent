import json
import base64
import os
from typing import Any, Dict, List
import aiofiles
from django.conf import settings
from pydantic_ai import RunContext
from constants.metabase_request_schemas import MetabaseAgentRequest, ViewingContext
from utils.chart_validators import (
    check_if_chart_is_valid,
    modify_chart_schema_if_necessary,
)
from utils.logging import metabase_helpers_logging
from utils.message_history import get_all_messages
from utils.metabase_api import MetabaseAPIService


logging = metabase_helpers_logging()
metabase_api = MetabaseAPIService()


async def navigate_user_to_view_chart(
    cnx: RunContext[MetabaseAgentRequest] , json_string_schema: str,
) -> str:

    try:
        json_data = json.loads(json_string_schema)

        message, valid = await check_if_chart_is_valid(json_data, cnx)

        if not valid:
            return message

        modified_json = await modify_chart_schema_if_necessary(json_data, cnx)

        chart_base_64 = base64.b64encode(json.dumps(modified_json).encode()).decode()

        if not chart_base_64.startswith("question#"):
            return f"question#{chart_base_64}"

        return chart_base_64
    except Exception as e:
        logging.error(f"Error in navigate_user_to_view_chart: {str(e)}")
        return f"Error: {str(e)}"


async def get_user_details_and_current_time(
    ctx: RunContext[MetabaseAgentRequest],
) -> str:

    user_data = await metabase_api.get_user_details(ctx.deps.user_id)

    if user_data is None:
        return "No user is currently logged in."

    email = user_data.get("email", "unknown")
    first_name = user_data.get("first_name", "unknown")
    last_name = user_data.get("last_name", "unknown")
    user_info = "The current logged in user is {} {} with email {}".format(
        first_name, last_name, email
    )
    current_time = ctx.deps.context.current_user_time.strftime("%B %d, %Y %H:%M:%S")
    return f"{user_info} and the current time is {current_time}"


async def get_chart_generation_schema_sample(
    cnx: RunContext[MetabaseAgentRequest],
) -> Dict[str, Any]:
    """This Function Gets The sample Schema For Chart Generation"""

    try:

        report_card_data_path = os.path.join(
            settings.BASE_DIR, "data", "cards_output.json"
        )

        async with aiofiles.open(report_card_data_path, mode="r") as f:

            content = await f.read()

        data = json.loads(content)

        user_is_viewing = cnx.deps.context.user_is_viewing

        if user_is_viewing is None:
            users_request = {}

        query = user_is_viewing[0].query

        if query is not None:
            users_request = query.model_dump_json()

        return {
            "sample_schema": data[:300],
            "users_request": users_request,
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": "resolve_get_chart_generation_schema_sample Failed ",
        }


async def get_messages_history(cnx: RunContext[MetabaseAgentRequest]):

    messages = await get_all_messages(cnx.deps.conversation_id)

    return messages


async def current_user_viewing_context(
    cnx: RunContext[MetabaseAgentRequest],
) -> List[ViewingContext]:

    if len(cnx.deps.context.user_is_viewing) == 0:
        return []

    return cnx.deps.context.user_is_viewing[0].model_dump_json()


async def current_user_chart_configs(cnx: RunContext[MetabaseAgentRequest]):

    user_is_viewing_list = cnx.deps.context.user_is_viewing or []

    if len(user_is_viewing_list) == 0:
        return []

    user_is_viewing = user_is_viewing_list[0]

    if user_is_viewing.chart_configs is None:

        return []

    if len(user_is_viewing.chart_configs) == 0:
        return []

    return user_is_viewing.chart_configs[0].model_dump_json()
