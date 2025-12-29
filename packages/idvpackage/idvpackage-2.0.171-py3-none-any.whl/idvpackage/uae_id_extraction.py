from pydantic import BaseModel, Field
import openai
import json

class UAEIDExtractionResult(BaseModel):
    is_header_verified: bool = Field(..., description="Is it the front side of a UAE ID?")
    id_number: str = Field(..., description="15-digit UAE ID number")

def extract_uae_front_id(base64_image: str) -> UAEIDExtractionResult:
    """
    Extracts UAE ID front fields using OpenAI's vision model and function calling.
    Args:
        openai_api_key (str): OpenAI API key.
        base64_image (str): Base64-encoded image of the UAE ID front.
    Returns:
        UAEIDExtractionResult: Extracted fields in Pydantic model.
    Raises:
        Exception: If extraction or parsing fails.
    """

    # Define the function schema for OpenAI function calling
    function_schema = {
        "name": "UAEIDExtractionResult",
        "description": "Extracts fields from the front side of a UAE ID card.",
        "parameters": {
            "type": "object",
            "properties": {
                "is_header_verified": {
                    "type": "boolean",
                    "description": "Is it the front side of a UAE ID?"
                },
                "id_number": {
                    "type": "string",
                    "description": "15-digit UAE ID number"
                }
            },
            "required": ["is_header_verified", "id_number"]
        }
    }
    prompt = (
        "You are an expert at extracting information from UAE ID cards. "
        "Given an image of the front side of a UAE ID, extract the relevant fields. "
        "If the id_number is not found, set it to an empty string. "
        "Set is_header_verified to true if the image is the front side of a UAE ID, else false."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            functions=[function_schema],
            function_call={"name": "UAEIDExtractionResult"},
            max_tokens=300
        )
        message = response.choices[0].message
        if message.function_call and message.function_call.arguments:
            args = json.loads(message.function_call.arguments)
            return UAEIDExtractionResult(**args)
        else:
            return {'error':'covered_photo'}
    except Exception as e:
        return {'error':'covered_photo'}
