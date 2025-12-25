from io import BytesIO

from joblib import Memory  # type: ignore[import-untyped]
from PIL import Image

from amsdal_server.configs.main import settings

memory = Memory(settings.THUMBNAIL_CACHE_PATH, verbose=0)


@memory.cache
def resize_image(image_bytes: bytes, size: tuple[int, int] | None = None) -> bytes:
    if not image_bytes or not size:
        return image_bytes

    # Load the image from bytes
    image = Image.open(BytesIO(image_bytes))

    # Calculate the aspect ratio
    width, height = image.size
    aspect_ratio = width / height

    # Calculate the new size while maintaining the aspect ratio
    new_width, new_height = size
    if new_width / new_height > aspect_ratio:
        new_width = int(new_height * aspect_ratio)
    else:
        new_height = int(new_width / aspect_ratio)

    # Resize the image
    image.thumbnail((new_width, new_height))

    # Convert the image to bytes
    output_stream = BytesIO()
    image.save(output_stream, format='PNG' if (image.mode or '').upper() == 'P' else 'JPEG')
    output_stream.seek(0)

    value = output_stream.getvalue()
    image.close()

    return value
