import os
from typing import Dict, Any
from django.conf import settings

import json
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from constants.metabase_request_schemas import MetabaseAgentRequest
from constants.prompt import SYSTEM_PROMPT
from tools.chart_tools import resolve_get_chart_or_dashboard_image
from tools.schema_tools import (
    resolve_database_schema,
    resolve_sample_data_from_viewing_context,
    resolve_table_schema_metadata,
)
from tools.sql_fixing_tools import (
    resolve_display_sql_in_editor,
    resolve_get_quey_data_to_fix_from_sql_error,
)
from tools.user_helper_tools import (
    resolve_current_user_viewing_context,
    resolve_get_chart_generation_schema_sample,
    resolve_navigate_user_to_view_chart,
    resolve_user_details_and_current_time,
    resolve_get_messages_history,
    resolver_current_user_chart_configs,
)
from utils.logging import metabase_helpers_logging
from django.conf import settings
from utils.message_history import (
    save_new_conversation,
    get_all_messages,
)

logging = metabase_helpers_logging()

if settings.OPENAI_API_KEY is not None:
    logging.info("OPENAI_API_KEY is  set in environment variables.")
    setattr(settings, 'USING_DEEPSEEK', False)
    model = OpenAIChatModel(
        "gpt-4o", provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY)
    )
elif settings.DEEPSEEK_API_KEY is not None:
    logging.info("DEEPSEEK_API_KEY is  set in environment variables.")
    setattr(settings, 'USING_DEEPSEEK', True)
    model = OpenAIChatModel(
        model_name="deepseek-chat",
        provider=OpenAIProvider(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1"),
    )    
else:
    logging.error(
        "No API key found in environment variables. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY."
    )
    raise ValueError(
        "No API key found in environment variables. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY."
    )

if getattr(settings, 'USING_DEEPSEEK', False) and not settings.GROQ_API_KEY:
    raise ValueError(
        "USING_DEEPSEEK is set to True but no GROQ_API_KEY found in environment variables. Please set GROQ_API_KEY as we use it for making calls to deepseek model for image analysis."
    )


analytics_agent = Agent(
    model,
    deps_type=MetabaseAgentRequest,
    system_prompt=SYSTEM_PROMPT,
)


@analytics_agent.tool
async def get_table_schema_metadata(
    ctx: RunContext[MetabaseAgentRequest],
) -> Dict[str, Any]:
    """
    Fetches detailed metadata for all tables in the DAT(Data Analytics Tool) instance.
    Returns a dictionary containing table metadata.
    If an error occurs, returns a dictionary with an error message.
    """
    return await resolve_table_schema_metadata(ctx)


@analytics_agent.tool
async def navigate_user_to_view_chart(
    cnx: RunContext[MetabaseAgentRequest], json_string_schema: str
) -> str:
    """
    Navigates the user to a specific chart view in DAT(Data Analytics Tool) using a Json chart schema.
    Returns a success message with the navigation URL.
    If an error occurs, returns an error message.
    """
    chart_url = await resolve_navigate_user_to_view_chart(json_string_schema, cnx)

    return chart_url


@analytics_agent.tool
async def get_sample_data_from_viewing_context(
    ctx: RunContext[MetabaseAgentRequest],
) -> Dict[str, Any]:
    """
    Fetches sample data for the current viewing context in DAT(Data Analytics Tool).
    Returns a dictionary containing sample data.
    If an error occurs, returns a dictionary with an error message.
    """

    return await resolve_sample_data_from_viewing_context(ctx)


@analytics_agent.tool
async def get_user_details_and_current_time(
    ctx: RunContext[MetabaseAgentRequest],
) -> str:
    """
    Fetches details of the current logged-in user from DAT(Data Analytics Tool) and returns a formatted string with user info and current time.
    If no user is logged in, returns a message indicating that.
    """

    return await resolve_user_details_and_current_time(ctx)


@analytics_agent.tool
async def get_quey_data_to_fix_from_sql_error(
    ctx: RunContext[MetabaseAgentRequest],
) -> Dict[str, Any]:
    """
    Fetches query data that needs to be fixed based on SQL errors in the current viewing context.
    Returns a dictionary containing the relevant query data.
    If an error occurs, returns a dictionary with an error message.
    """

    return await resolve_get_quey_data_to_fix_from_sql_error(ctx)


@analytics_agent.tool
async def get_database_schema(ctx: RunContext[MetabaseAgentRequest]) -> Dict[str, Any]:
    """
    Retrieve the database schema for the current DAT(Data Analytics Tool) instance or the
    viewing context provided by the agent request.

    """
    return await resolve_database_schema(ctx)


@analytics_agent.tool
async def get_chart_generation_schema_sample(
    ctx: RunContext[MetabaseAgentRequest],
) -> Dict[str, Any]:
    """
    Return a small schema sample useful for generating chart payloads.

    """

    return await resolve_get_chart_generation_schema_sample(ctx)


@analytics_agent.tool
async def get_chart_or_dashboard_image(ctx: RunContext[MetabaseAgentRequest]):
    """
    Produce a chart or dashboard image (or a Base64-encoded payload) for the
    current viewing context or a supplied chart definition.
    """

    return await resolve_get_chart_or_dashboard_image(ctx)


@analytics_agent.tool
async def current_user_viewing_context(ctx: RunContext[MetabaseAgentRequest]):
    """
    Return the current viewing context for the logged-in user.
    """
    data = await resolve_current_user_viewing_context(ctx)

    if len(data) == 0:
        return "NO content Found"

    return data


@analytics_agent.tool
async def current_user_chart_configs(ctx: RunContext[MetabaseAgentRequest]):
    """
    Fetch chart configuration presets or user-specific chart preferences.
    """

    return resolver_current_user_chart_configs(ctx)


@analytics_agent.tool
async def get_messages_history(
    ctx: RunContext[MetabaseAgentRequest],
):
    """
    Retrieve recent message history for the current conversation.
    """

    return await resolve_get_messages_history(ctx)


@analytics_agent.tool
async def display_fixed_sql_in_editor(
    ctx: RunContext[MetabaseAgentRequest], fixed_sql: str
):
    """Display Fixed sql to the users sql Editor this fuction receives the fixed_sql as an argument"""

    data = await resolve_display_sql_in_editor(ctx, fixed_sql)

    if not data["success"]:
        return "error Occured While displaying sql"

    return "sql_fixed#" + data["base_64_context"]


async def analytics_steaming_agent(user_data: MetabaseAgentRequest):

    # Create a queue for the event_stream_handler to push wire-format lines into.

    try:

        message_history = await get_all_messages(user_data.conversation_id)

        async with analytics_agent.iter(
            user_data.messages[0].content,
            deps=user_data,
            message_history=message_history,
        ) as run:

            async for node in run:
                if Agent.is_user_prompt_node(node):
                    # put thinking here
                    logging.info(f"UserPromptNode: {node.user_prompt}")

                elif Agent.is_model_request_node(node):
                    logging.info(
                        "=== ModelRequestNode: streaming partial request tokens ==="
                    )

                    async with node.stream(run.ctx) as request_stream:
                        final_result_found = False
                        async for event in request_stream:

                            if isinstance(event, PartStartEvent):
                                logging.info(f"PartStartEvent: {event.part}")

                            elif isinstance(event, PartDeltaEvent):
                                if isinstance(event.delta, TextPartDelta):
                                    logging.info(
                                        f"TextPartDelta: {event.delta.content_delta}"
                                    )
                                    yield f"0:{json.dumps({'type': 'text', 'value': event.delta.content_delta})}\n\n"

                                elif isinstance(event.delta, ThinkingPartDelta):
                                    logging.info(
                                        f"ThinkingPartDelta: {event.delta.content_delta}"
                                    )
                                    yield f"0:{json.dumps({'type': 'text', 'value': event.delta.content_delta})}\n\n"

                                elif isinstance(event.delta, ToolCallPartDelta):
                                    logging.info(
                                        f"ToolCallPartDelta: {event.delta.tool_name_delta}({event.delta.tool_call_id})"
                                    )
                                    payload = {
                                        "toolCallId": event.delta.tool_call_id,
                                        "toolName": event.delta.tool_name_delta or " ",
                                        "args": event.delta.args_delta or {},
                                    }
                                    yield f"9:{json.dumps(payload)}\n\n"

                            elif isinstance(event, FinalResultEvent):
                                logging.info(f"FinalResultEvent: {event.tool_name}")
                                yield f"d:{json.dumps({'finishReason': 'stop', 'usage': {'promptTokens': 0 ,'completionTokens': 0}})}\n\n"
                                final_result_found = True
                                break

                        if final_result_found:
                            previous_text = ""
                            async for output in request_stream.stream_text():
                                current_text = output.replace(previous_text, "")
                                logging.info(
                                    f"Current Text output text Here: {current_text}"
                                )
                                previous_text = output
                                yield f"0:{json.dumps({'type': 'text', 'value': current_text})}\n\n"

                elif Agent.is_call_tools_node(node):
                    # A handle-response node => The model returned some data, potentially calls a tool
                    logging.info(
                        "=== CallToolsNode: streaming partial response & tool usage ==="
                    )
                    async with node.stream(run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                logging.info(
                                    f"[Tools] Calling tool {event.part.tool_name}({event.part.args}) with call ID {event.tool_call_id!r}"
                                )
                                payload = {
                                    "toolCallId": event.tool_call_id,
                                    "toolName": event.part.tool_name or " ",
                                    "args": event.part.args or {},
                                }
                                yield f"9:{json.dumps(payload)}\n\n"
                            elif isinstance(event, FunctionToolResultEvent):
                                logging.info(
                                    f"[Tools] Tool call {event.tool_call_id!r} returned => {event.result.has_content()}"
                                )

                                if "question" in event.result.content:
                                    logging.info(f"Navigating to chart with content:")
                                    yield f"2:{json.dumps({'type':'navigate_to','version':1,'value':f'/{event.result.content}'})}\n\n"

                                if "sql_fixed#" in event.result.content:
                                    if isinstance(event.result.content, str):
                                        logging.info(f"Displaying sql to the user")
                                        yield f"2:{json.dumps({'type':'navigate_to','version':1,'value':f'/{event.result.content.replace("sql_fixed" , "question")}'})}\n\n"

                                else:
                                    logging.info(
                                        f"Tool result content: Called Normal Tool"
                                    )
                                    yield f"a:{json.dumps({'toolCallId': event.tool_call_id, 'result': event.result.content})}\n\n"

                elif Agent.is_end_node(node):
                    # Once an End node is reached, the agent run is complete
                    assert run.result is not None
                    assert run.result.output == node.data.output
                    logging.info(
                        f"=== EndNode: Agent run complete with output: {run.result.output} ==="
                    )
                    all_messages = run.result.new_messages_json().decode()

                    await save_new_conversation(user_data.conversation_id, all_messages)

                    yield f"d:{json.dumps({'finishReason': 'stop', 'usage': {'promptTokens': 0, 'completionTokens': 0}})}\n\n"
    except Exception as e:
        logging.error(e)
        yield f"0:{json.dumps({'type': 'text', 'value': "Oops an error occurred while Performing That , Please Would You try Again"})}\n\n"
