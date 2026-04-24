import pyvips
import asyncio


def compress_image_bytes(data: bytes, quality: int = 60) -> bytes:
    image = pyvips.Image.new_from_buffer(data, "", access="sequential")

    compressed = image.write_to_buffer(
        ".jpg",
        Q=quality,
        optimize_coding=True
    )

    return compressed



async def compress_image_async(data: bytes, quality: int = 50) -> bytes:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        compress_image_bytes,
        data,
        quality
    )