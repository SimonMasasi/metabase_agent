from metabase_agent_helper.models import MessagesHistory
from asgiref.sync import sync_to_async
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage

from utils.logging import metabase_helpers_logging


logging = metabase_helpers_logging()


async def get_all_messages(conversation_id:str) -> list[ModelMessage]:

    logging.info(f"getting of Messages Started")

    # Evaluate the queryset inside a thread via sync_to_async to avoid
    # Django's SynchronousOnlyOperation when called from async code.
    all_messages = await sync_to_async(list)(
        MessagesHistory.objects.filter(conversation_id=conversation_id)
    )

    messages: list[ModelMessage] = []

    if len(all_messages) > 2:
        all_messages = all_messages[:1]

    for message in all_messages:
        messages.extend(ModelMessagesTypeAdapter.validate_json(message.messages_json))

    logging.info("all Messages Returned successfully")

    return messages


async def save_new_conversation(conversation_id:str, messages:str):

    logging.info("Creating of Messages Started")

    await MessagesHistory.objects.acreate(
        conversation_id=conversation_id, messages_json=messages
    )

    logging.info("Creating of Messages Finished")

    return True
