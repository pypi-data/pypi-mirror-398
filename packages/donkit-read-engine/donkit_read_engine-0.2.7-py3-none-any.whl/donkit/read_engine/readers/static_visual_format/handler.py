import base64

from ..static_visual_format.models import (
    get_image_analysis_service,
)


def image_read_handler(path: str) -> dict[str, list[dict[str, str | int]]]:
    """Processes and extracts information from an image file.

    The image is loaded, encoded in base64 format, and passed to a model
    for further processing to recognize and extract content.

    :param path: Path to the image file
    :return: A string containing the result of processing the image (e.g., recognized text or objects)
    """
    # Open the image file in binary mode for reading
    with open(path, "rb") as image_file:
        # Read the image as bytes and encode it to base64 for easier transmission
        image_bytes: bytes = base64.b64encode(image_file.read())

        # Convert the base64 bytes to a UTF-8 string
        encoded_image: str = image_bytes.decode("utf-8")

        # Placeholder: Image content types that could be processed include:
        # - Graphs
        # - Diagrams
        # - Tables
        # - Text
        # - Flowcharts
        # - Scanned documents
        # The actual model (qwen2_vl_7b_model) will be responsible for distinguishing these types.

        # Call the model for image processing, using the base64-encoded image string
        # qwen2_vl_7b_model is assumed to be the model that performs OCR or visual recognition
        image_analysis_service = get_image_analysis_service()
        result: str = image_analysis_service.analyze_image(encoded_image)

        # Return the processed result (e.g., recognized text, labels, etc.)
        return {
            "content": [
                {
                    "page": 0,
                    "type": "Image",
                    "content": result,
                }
            ],
        }
