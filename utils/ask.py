from openai import OpenAI
from django.conf import settings

# Initialize the OpenAI client with the API key from Django settings



def get_metabot_response(metabase_request: dict, model: str = "gpt-4o") -> list:
    """
    Generates a response from an LLM for the DAT (Data Analytics Tool) Bot based on user input and context.

    Args:
        metabase_request (dict): The request from DAT containing messages and optional context.
        model (str): The LLM model to use (default: "gpt-4o").

    Returns:
        list: A list of message dictionaries including the conversation history and assistant's reply,
              formatted as [{"role": str, "content": str, "navigate_to": None}].
    """
    # Extract conversation history from the request
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    messages = metabase_request.get("messages", [])

    # Extract optional context about what the user is viewing
    context = metabase_request.get("context", {})

    # Build a concise system prompt with relevant context
    system_prompt = (
        "You are a helpful assistant for Metabase, a data analysis platform."
    )
    if context:
        system_prompt += f" The user is working with database {context}."
    if context:
        system_prompt += " They are viewing the results of a specific query."

    # Prepare the message list for the LLM: system prompt + conversation history
    messages_for_api = [{"role": "system", "content": system_prompt}] + messages

    # Call the LLM API and handle potential errors
    try:
        response = client.chat.completions.create(
            model=model, messages=messages_for_api
        )
        assistant_reply = response.choices[0].message.content.strip()
    except Exception as e:
        assistant_reply = f"Error: Unable to get response from LLM - {str(e)}"

    # Format the response for Metabase: include original messages + assistant's reply
    response_messages = [
        {
            "role": msg["role"],
            "content": msg["content"],
            "navigate_to": msg.get("navigate_to", None),
        }
        for msg in messages
    ]
    response_messages.append(
        {"role": "assistant", "content": assistant_reply, "navigate_to": None}
    )

    return response_messages
