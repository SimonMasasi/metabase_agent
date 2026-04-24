from django.conf import settings
import base64
import magic
from pydantic_ai import RunContext
from constants.metabase_request_schemas import MetabaseAgentRequest
from utils.logging import metabase_helpers_logging
from utils.image_utils import compress_image_async
from utils.image_ai_completion import get_analysis_from_image_groq
from utils.metabase_api import MetabaseAPIService
from pydantic_ai import BinaryContent
import cairosvg


logging = metabase_helpers_logging()
metabase_api = MetabaseAPIService()


async def resolve_get_chart_or_dashboard_image(
    ctx: RunContext[MetabaseAgentRequest],
) -> BinaryContent | str:

    try: 

        NO_IMAGE_FOUND = "no image Found"

        user_is_viewing = ctx.deps.context.user_is_viewing

        if user_is_viewing is None or len(user_is_viewing) == 0:
            return NO_IMAGE_FOUND

        user_is_viewing_data = user_is_viewing[0]

        if user_is_viewing_data.type == "dashboard":

            chart_base_64 = user_is_viewing_data.dashboard_image or None

            if not chart_base_64:
                return NO_IMAGE_FOUND

            if "base64," in chart_base_64:
                image_base_64 = chart_base_64.split("base64,")[1]
            else:
                image_base_64 = chart_base_64

            image_decoded_bytes = base64.b64decode(image_base_64)

            #compress the image bytes to reduce size and improve performance
            compressed_image_bytes = await compress_image_async(image_decoded_bytes)

            file_type = magic.from_buffer(compressed_image_bytes, mime=True)
            if getattr(settings, 'USING_DEEPSEEK', False):
                logging.info("===================== using deepseek for image analysis return image change image to base64 then send it to groq  =====================")
                image_base_64 = base64.b64encode(compressed_image_bytes).decode("utf-8")
                groq_response = await get_analysis_from_image_groq(f"data:{file_type};base64,{image_base_64}")
                return groq_response

            return BinaryContent(compressed_image_bytes, media_type=file_type)

        if (
            user_is_viewing_data.type == "question"
            or user_is_viewing_data.type == "adhoc"
        ):

            chart_configs = user_is_viewing_data.chart_configs

            if chart_configs is None or len(chart_configs) == 0:
                return NO_IMAGE_FOUND

            chart_config_data = chart_configs[0]

            chart_base_64 = chart_config_data.image_base_64

            if chart_base_64 is None:
                return NO_IMAGE_FOUND

            if "base64" in chart_base_64:
                image_base_64 = chart_base_64.split("base64,")[1]
            else:
                image_base_64 = chart_base_64

            image_decoded_bytes = base64.b64decode(image_base_64)

            #compress the image bytes to reduce size and improve performance
            compressed_image_bytes = await compress_image_async(image_decoded_bytes)

            file_type = magic.from_buffer(compressed_image_bytes, mime=True)

            if chart_base_64.startswith("data:image/svg+xml"):
                logging.info("===================== changing svg to png =====================")
                png_bytes = cairosvg.svg2png(bytestring=image_decoded_bytes)

                if png_bytes is None:
                    return NO_IMAGE_FOUND

                image_decoded_bytes = png_bytes
                file_type = "image/png"

            if getattr(settings, 'USING_DEEPSEEK', False):
                logging.info("===================== using deepseek for image analysis return image change image to base64 then send it to groq  =====================")
                image_base_64 = base64.b64encode(image_decoded_bytes).decode("utf-8")
                groq_response = await get_analysis_from_image_groq(f"data:{file_type};base64,{image_base_64}")
                return groq_response

            return BinaryContent(image_decoded_bytes, media_type=file_type)

        else:
            return NO_IMAGE_FOUND

    except Exception as e:
        logging.error(f"Error Occurred  Failed To Fetch Image Chart or Dashboard {e}")

        return NO_IMAGE_FOUND
