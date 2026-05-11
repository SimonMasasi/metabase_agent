

from django.conf import settings
from .logging import metabase_agent_logging
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

logging = metabase_agent_logging()

def get_model_provider():
    if settings.OPENAI_API_KEY is not None:
        logging.info("OPENAI_API_KEY is  set in environment variables.")
        setattr(settings, 'USING_DEEPSEEK', False)
        return OpenAIChatModel(
            "gpt-4o", provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        )
    elif settings.DEEPSEEK_API_KEY is not None:
        logging.info("DEEPSEEK_API_KEY is  set in environment variables.")
        setattr(settings, 'USING_DEEPSEEK', True)
        return OpenAIChatModel(
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