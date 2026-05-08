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

from constants.dashboard_prompt import DASHBOARD_ANALYTICS_PROMPT

from constants.metabase_request_schemas import DashboardAnalysisRequest
from utils.logging import metabase_helpers_logging
from django.conf import settings
from utils.message_history import (
    save_new_conversation,
    get_all_messages,
)

logging = metabase_helpers_logging()

if settings.OPENAI_API_KEY is not None:
    setattr(settings, 'USING_DEEPSEEK', False)

    logging.info("OPENAI_API_KEY is  set in environment variables.")
    model = OpenAIChatModel(
        "gpt-4o", provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY)
    )
elif settings.DEEPSEEK_API_KEY is not None:
    logging.info("DEEPSEEK_API_KEY is  set in environment variables.")
    model = OpenAIChatModel(
        model_name="deepseek-chat",
        provider=OpenAIProvider(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1"),
    )
    setattr(settings, 'USING_DEEPSEEK', True)
else:
    logging.error(
        "No API key found in environment variables. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY."
    )
    raise ValueError(
        "No API key found in environment variables. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY."
    )



analytics_agent = Agent(
    model,
    deps_type=DashboardAnalysisRequest,
    system_prompt=DASHBOARD_ANALYTICS_PROMPT,
)


async def dashboard_steaming_agent(user_data: DashboardAnalysisRequest):

    # Create a queue for the event_stream_handler to push wire-format lines into.

    try:

        message_history = await get_all_messages(user_data.conversation_id)

        if user_data.message is None:
            message = "Analyze the dashboard data and provide insights."
        else:
            message = user_data.message

        message_with_json = f"{message} {json.dumps([detail.model_dump_json() for detail in user_data.dashboard_data])}"

        async with analytics_agent.iter(
            message_with_json,
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
                                    yield f"{json.dumps({'type': 'text', 'value': event.delta.content_delta})}\n\n"

                                elif isinstance(event.delta, ThinkingPartDelta):
                                    logging.info(
                                        f"ThinkingPartDelta: {event.delta.content_delta}"
                                    )
                                    yield f"{json.dumps({'type': 'text', 'value': event.delta.content_delta})}\n\n"

                                elif isinstance(event.delta, ToolCallPartDelta):
                                    logging.info(
                                        f"ToolCallPartDelta: {event.delta.tool_name_delta}({event.delta.tool_call_id})"
                                    )
                                    payload = {
                                        "toolCallId": event.delta.tool_call_id,
                                        "toolName": event.delta.tool_name_delta or " ",
                                        "args": event.delta.args_delta or {},
                                    }
                                    yield f"{json.dumps(payload)}\n\n"

                            elif isinstance(event, FinalResultEvent):
                                logging.info(f"FinalResultEvent: {event.tool_name}")
                                yield f"{json.dumps({'finishReason': 'stop', 'usage': {'promptTokens': 0 ,'completionTokens': 0}})}\n\n"
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
                                yield f"{json.dumps({'type': 'text', 'value': current_text})}\n\n"

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
                                yield f"{json.dumps(payload)}\n\n"
                            elif isinstance(event, FunctionToolResultEvent):
                                logging.info(
                                    f"[Tools] Tool call {event.tool_call_id!r} returned => {event.result.has_content()}"
                                )

                                if "question" in event.result.content:
                                    logging.info(f"Navigating to chart with content:")
                                    yield f"{json.dumps({'type':'navigate_to','version':1,'value':f'/{event.result.content}'})}\n\n"

                                if "sql_fixed#" in event.result.content:
                                    logging.info(f"Displaying sql to the user")
                                    yield f"{json.dumps({'type':'navigate_to','version':1,'value':f'/{event.result.content.replace("sql_fixed" , "question")}'})}\n\n"

                                else:
                                    logging.info(
                                        f"Tool result content: Called Normal Tool"
                                    )
                                    yield f"{json.dumps({'toolCallId': event.tool_call_id, 'result': event.result.content})}\n\n"

                elif Agent.is_end_node(node):
                    # Once an End node is reached, the agent run is complete
                    assert run.result is not None
                    assert run.result.output == node.data.output
                    logging.info(
                        f"=== EndNode: Agent run complete with output: {run.result.output} ==="
                    )
                    all_messages = run.result.new_messages_json().decode()

                    await save_new_conversation(user_data.conversation_id, all_messages)

                    yield f"{json.dumps({'finishReason': 'stop', 'usage': {'promptTokens': 0, 'completionTokens': 0}})}\n\n"
    except Exception as e:
        logging.error(e)
        yield f"{json.dumps({'type': 'text', 'value': "Oops an error occurred while Performing That , Please Would You try Again"})}\n\n"



async def dashboard_agent_non_stream(
    user_data: DashboardAnalysisRequest,
) -> str | None:
    try:
        message_history = await get_all_messages(user_data.conversation_id)

        if user_data.message is None:
            message = "Analyze the dashboard data and provide insights."
        else:
            message = user_data.message

        message_with_json = f"{message} {json.dumps([detail.model_dump_json() for detail in user_data.dashboard_data])}"

        answer = await analytics_agent.run(
            message_with_json,
            deps=user_data,
            message_history=message_history,
        )

        all_messages = answer.new_messages_json().decode()

        await save_new_conversation(user_data.conversation_id, all_messages)

        return answer.output
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return None