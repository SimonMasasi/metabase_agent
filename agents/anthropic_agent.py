import json
from uuid import uuid4
from pydantic_ai.exceptions import ModelAPIError

from pydantic_ai import Agent
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

from constants.metabase_request_schemas import MetabaseAgentRequest
from constants.prompt import SYSTEM_PROMPT
from tools.chart_tools import get_chart_or_dashboard_image
from tools.schema_tools import (
	get_database_schema,
	get_sample_data_from_viewing_context,
	get_table_schema_metadata,
)
from tools.sql_fixing_tools import (
	display_fixed_sql_in_editor,
	get_quey_data_to_fix_from_sql_error,
)
from tools.user_helper_tools import (
	current_user_chart_configs,
	current_user_viewing_context,
	get_chart_generation_schema_sample,
	get_messages_history,
	get_user_details_and_current_time,
	navigate_user_to_view_chart,
)
from utils.logging import metabase_agent_logging
from utils.message_history import get_all_messages, save_new_conversation
from utils.model_provider import get_model_provider

logging = metabase_agent_logging()
model = get_model_provider()

tool_sets = [
	get_table_schema_metadata,
	navigate_user_to_view_chart,
	get_sample_data_from_viewing_context,
	get_user_details_and_current_time,
	get_quey_data_to_fix_from_sql_error,
	get_chart_generation_schema_sample,
	get_database_schema,
	get_chart_or_dashboard_image,
	current_user_viewing_context,
	current_user_chart_configs,
	get_messages_history,
	display_fixed_sql_in_editor,
]

anthropic_streaming_agent = Agent(
	model,
	deps_type=MetabaseAgentRequest,
	system_prompt=SYSTEM_PROMPT,
	tools=tool_sets,
)


def _anthropic_sse_event(event_name, payload):
	return f"event: {event_name}\\ndata: {json.dumps(payload)}\\n\\n"


def _message_stop_events():
	yield _anthropic_sse_event(
		"content_block_stop",
		{"type": "content_block_stop", "index": 0},
	)
	yield _anthropic_sse_event(
		"message_delta",
		{
			"type": "message_delta",
			"delta": {"stop_reason": "end_turn", "stop_sequence": None},
			"usage": {"output_tokens": 0},
		},
	)
	yield _anthropic_sse_event("message_stop", {"type": "message_stop"})


async def anthropic_streaming_agent_runner(user_data: MetabaseAgentRequest):
	message_id = f"msg_{uuid4().hex}"
	content_open = False
	stop_sent = False

	def _open_content_block_if_needed():
		nonlocal content_open
		if not content_open:
			content_open = True
			return _anthropic_sse_event(
				"content_block_start",
				{
					"type": "content_block_start",
					"index": 0,
					"content_block": {"type": "text", "text": ""},
				},
			)
		return None

	try:
		yield _anthropic_sse_event(
			"message_start",
			{
				"type": "message_start",
				"message": {
					"id": message_id,
					"type": "message",
					"role": "assistant",
					"content": [],
					"model": user_data.model,
					"stop_reason": None,
					"stop_sequence": None,
					"usage": {"input_tokens": 0, "output_tokens": 0},
				},
			},
		)

		message_history = await get_all_messages(user_data.conversation_id)

		max_attempts = 2
		for attempt in range(max_attempts):
			try:
				async with anthropic_streaming_agent.iter(
					user_data.messages[0].content[0].text,
					deps=user_data,
					message_history=message_history,
				) as run:
					async for node in run:
						if Agent.is_user_prompt_node(node):
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
											open_event = _open_content_block_if_needed()
											if open_event is not None:
												yield open_event
											yield _anthropic_sse_event(
												"content_block_delta",
												{
													"type": "content_block_delta",
													"index": 0,
													"delta": {
														"type": "text_delta",
														"text": event.delta.content_delta,
													},
												},
											)

										elif isinstance(event.delta, ThinkingPartDelta):
											logging.info(
												f"ThinkingPartDelta: {event.delta.content_delta}"
											)
											open_event = _open_content_block_if_needed()
											if open_event is not None:
												yield open_event
											yield _anthropic_sse_event(
												"content_block_delta",
												{
													"type": "content_block_delta",
													"index": 0,
													"delta": {
														"type": "text_delta",
														"text": event.delta.content_delta,
													},
												},
											)

										elif isinstance(event.delta, ToolCallPartDelta):
											logging.info(
												f"ToolCallPartDelta: {event.delta.tool_name_delta}({event.delta.tool_call_id})"
											)

									elif isinstance(event, FinalResultEvent):
										logging.info(f"FinalResultEvent: {event.tool_name}")
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
										if current_text:
											open_event = _open_content_block_if_needed()
											if open_event is not None:
												yield open_event
											yield _anthropic_sse_event(
												"content_block_delta",
												{
													"type": "content_block_delta",
													"index": 0,
													"delta": {
														"type": "text_delta",
														"text": current_text,
													},
												},
											)

						elif Agent.is_call_tools_node(node):
							logging.info(
								"=== CallToolsNode: streaming partial response & tool usage ==="
							)
							async with node.stream(run.ctx) as handle_stream:
								async for event in handle_stream:
									if isinstance(event, FunctionToolCallEvent):
										logging.info(
											f"[Tools] Calling tool {event.part.tool_name}({event.part.args}) with call ID {event.tool_call_id!r}"
										)
									elif isinstance(event, FunctionToolResultEvent):
										logging.info(
											f"[Tools] Tool call {event.tool_call_id!r} returned => {event.result.has_content()}"
										)

						elif Agent.is_end_node(node):
							assert run.result is not None
							assert run.result.output == node.data.output
							logging.info(
								f"=== EndNode: Agent run complete with output: {run.result.output} ==="
							)
							all_messages = run.result.new_messages_json().decode()
							await save_new_conversation(user_data.conversation_id, all_messages)
							open_event = _open_content_block_if_needed()
							if open_event is not None:
								yield open_event
							for stop_event in _message_stop_events():
								yield stop_event
							stop_sent = True
							break

				break
			except ModelAPIError as e:
				is_last_attempt = attempt == (max_attempts - 1)
				if content_open or is_last_attempt:
					raise
				logging.warning(
					f"Transient model connection error, retrying once: {type(e).__name__}: {str(e)}"
				)
				continue

	except Exception as e:
		logging.error(
			f"Error in anthropic_streaming_agent_runner: {type(e).__name__}: {str(e)}",
			stack_info=True,
		)
		open_event = _open_content_block_if_needed()
		if open_event is not None:
			yield open_event
		yield _anthropic_sse_event(
			"content_block_delta",
			{
				"type": "content_block_delta",
				"index": 0,
				"delta": {
					"type": "text_delta",
					"text": "Oops an error occurred while performing that request, please try again.",
				},
			},
		)
		for stop_event in _message_stop_events():
			yield stop_event
		stop_sent = True

	if not stop_sent:
		open_event = _open_content_block_if_needed()
		if open_event is not None:
			yield open_event
		for stop_event in _message_stop_events():
			yield stop_event
