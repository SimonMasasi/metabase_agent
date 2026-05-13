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
from tools.chart_tools import get_chart_or_dashboard_image, structured_output
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
	structured_output
]

anthropic_streaming_agent = Agent(
	model,
	deps_type=MetabaseAgentRequest,
	system_prompt=SYSTEM_PROMPT,
	tools=tool_sets,
)


def _extract_json_from_text(text: str) -> dict | None:
	if not text:
		return None

	candidate = text.strip()
	if candidate.startswith("```"):
		lines = candidate.splitlines()
		if lines and lines[0].startswith("```"):
			lines = lines[1:]
		if lines and lines[-1].strip() == "```":
			lines = lines[:-1]
		candidate = "\n".join(lines).strip()

	try:
		parsed = json.loads(candidate)
		if isinstance(parsed, dict):
			return parsed
	except Exception:
		return None

	return None


def _requested_structured_tool_name(user_data: MetabaseAgentRequest) -> str | None:
	tool_choice = user_data.tool_choice or {}
	if isinstance(tool_choice, dict):
		name = tool_choice.get("name")
		if isinstance(name, str) and name.strip():
			return name.strip()

	for tool in user_data.tools or []:
		if isinstance(tool, dict):
			name = tool.get("name")
			if isinstance(name, str) and name.strip().lower() == "structured_output":
				return name.strip()

	return None


def _get_latest_user_prompt(user_data: MetabaseAgentRequest) -> str:
	# pydantic-ai expects a single prompt (string/message parts), not the full API message list.
	for message in reversed(user_data.messages):
		if message.role == "user" and message.content:
			text_parts = [part.text for part in message.content if getattr(part, "text", None)]
			if text_parts:
				return "\n".join(text_parts)

	return ""


def _anthropic_sse_event(event_name, payload):
	# SSE frames must use real newlines; escaped "\\n" breaks downstream parsers.
	return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"


def _message_stop_events(stop_reason: str = "end_turn", include_content_block_stop: bool = True):
	if include_content_block_stop:
		yield _anthropic_sse_event(
			"content_block_stop",
			{"type": "content_block_stop", "index": 0},
		)
	yield _anthropic_sse_event(
		"message_delta",
		{
			"type": "message_delta",
			"delta": {"stop_reason": stop_reason, "stop_sequence": None},
			"usage": {"output_tokens": 0},
		},
	)
	yield _anthropic_sse_event("message_stop", {"type": "message_stop"})


def _extract_structured_tool_payload(
	run_output,
	buffered_text: str,
	structured_tool_name: str,
) -> dict | None:
	if isinstance(run_output, dict):
		return run_output

	if isinstance(run_output, list) and structured_tool_name == "structured_output":
		if all(isinstance(item, str) for item in run_output):
			return {"questions": run_output}

	if isinstance(run_output, str):
		parsed = _extract_json_from_text(run_output)
		if isinstance(parsed, dict):
			return parsed

	if hasattr(run_output, "model_dump"):
		try:
			dumped = run_output.model_dump()
			if isinstance(dumped, dict):
				return dumped
		except Exception:
			pass

	parsed_from_text = _extract_json_from_text(buffered_text)
	if isinstance(parsed_from_text, dict):
		return parsed_from_text

	# Last-resort fallback for strict structured callers expecting a tool call.
	if structured_tool_name == "structured_output":
		return {"questions": []}

	return None


def _coerce_tool_args_to_dict(raw_args) -> dict:
	if isinstance(raw_args, dict):
		return raw_args

	if hasattr(raw_args, "model_dump"):
		try:
			dumped = raw_args.model_dump()
			if isinstance(dumped, dict):
				return dumped
		except Exception:
			pass

	if isinstance(raw_args, str):
		parsed = _extract_json_from_text(raw_args)
		if isinstance(parsed, dict):
			return parsed

	return {}


async def anthropic_streaming_agent_runner(user_data: MetabaseAgentRequest):
	message_id = f"msg_{uuid4().hex}"
	content_open = False
	stop_sent = False
	text_emitted = False
	tool_use_emitted = False
	structured_tool_name = _requested_structured_tool_name(user_data)
	structured_mode = structured_tool_name is not None
	buffered_text = ""

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

	def _emit_text_delta(text):
		nonlocal text_emitted, buffered_text
		if not text:
			return None
		if structured_mode:
			buffered_text += text
			return None
		text_emitted = True
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
					"text": text,
				},
			},
		)

	def _emit_tool_use_content_block(tool_name: str, tool_input: dict, index: int = 0):
		nonlocal tool_use_emitted
		tool_use_emitted = True
		tool_input = tool_input or {}
		yield _anthropic_sse_event(
			"content_block_start",
			{
				"type": "content_block_start",
				"index": index,
				"content_block": {
					"type": "tool_use",
					"id": f"toolu_{uuid4().hex}",
					"name": tool_name,
					"input": {},
				},
			},
		)
		yield _anthropic_sse_event(
			"content_block_delta",
			{
				"type": "content_block_delta",
				"index": index,
				"delta": {
					"type": "input_json_delta",
					"partial_json": json.dumps(tool_input),
				},
			},
		)
		yield _anthropic_sse_event(
			"content_block_stop",
			{"type": "content_block_stop", "index": index},
		)

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
				user_prompt = _get_latest_user_prompt(user_data)
				async with anthropic_streaming_agent.iter(
					user_prompt=user_prompt,
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
											for sse_event in _emit_text_delta(event.delta.content_delta) or []:
												yield sse_event

										elif isinstance(event.delta, ThinkingPartDelta):
											logging.info(
												f"ThinkingPartDelta: {event.delta.content_delta}"
											)
											if not structured_mode:
												for sse_event in _emit_text_delta(event.delta.content_delta):
													yield sse_event

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
											for sse_event in _emit_text_delta(current_text) or []:
												yield sse_event

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
										if structured_mode and event.part.tool_name == (structured_tool_name or "structured_output"):
											tool_args = _coerce_tool_args_to_dict(event.part.args)
											for sse_event in _emit_tool_use_content_block(event.part.tool_name, tool_args):
												yield sse_event
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
							if not text_emitted:
								final_text = str(run.result.output or "")
								for sse_event in _emit_text_delta(final_text) or []:
									yield sse_event

							if structured_mode and not tool_use_emitted:
								tool_payload = _extract_structured_tool_payload(
									run.result.output,
									buffered_text,
									structured_tool_name or "structured_output",
								)
								if isinstance(tool_payload, dict):
									for sse_event in _emit_tool_use_content_block(
										structured_tool_name or "structured_output", tool_payload
									):
										yield sse_event
							all_messages = run.result.new_messages_json().decode()
							await save_new_conversation(user_data.conversation_id, all_messages)
							if not tool_use_emitted:
								open_event = _open_content_block_if_needed()
								if open_event is not None:
									yield open_event
							for stop_event in _message_stop_events(
								"tool_use" if tool_use_emitted else "end_turn",
								include_content_block_stop=not tool_use_emitted,
							):
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
