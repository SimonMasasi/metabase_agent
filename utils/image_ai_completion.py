import asyncio

from openai import OpenAI
from django.conf import settings
from groq import Groq



def get_analysis_from_image(prompt: str, base64_image:str, model: str = "gpt-4.1" ):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)


    """
    Generate an AI completion for a given image prompt using OpenAI's API.

    Args:
        prompt (str): The image prompt to generate a completion for.
        model (str): The model to use for the completion. Default is "gpt-4.1".

    Returns:
        str: The generated completion text.
    """

    image = base64_image if "data:image/" in base64_image else f"data:image/png;base64,{base64_image}"
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"{image}",
                    },
                ],
            }
        ],
    )

    return response.output_text




async def get_analysis_from_image_groq(base64_image: str):
    client = Groq(api_key=settings.GROQ_API_KEY)

    def _call_groq():
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "analyze the following image and provide insights about the trends shown in the chart, the x and y axis labels, and any other relevant information that can be derived from the image. Be as detailed as possible in your analysis."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image
                            }
                        }
                    ]
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
        )

        return completion.choices[0].message.content

    return await asyncio.to_thread(_call_groq)
