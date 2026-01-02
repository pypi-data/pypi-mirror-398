import os
from google import genai
from google.genai import types


def generate(torrent: str, subtitle: str):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"""torrent: {torrent}
subtitle: {subtitle}"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,
        ),
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["subtitle", "torrent", "is_match", "reason"],
            properties = {
                "subtitle": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "torrent": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "is_match": genai.types.Schema(
                    type = genai.types.Type.BOOLEAN,
                ),
                "reason": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""You are an expert at matching subtitle names with torrent names. Resolution and codecs are not important. Consider the release group when matching, however it is not the most important thing. You always output a JSON in the following format:

{
  \"subtitle\": string,
  \"torrent\": string,
  \"is_match\": boolean,
  \"reason\": string
}"""),
        ],
    )

    # Initialize an empty string to store the full response
    full_response_text = ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        # Append each chunk's text to the string
        full_response_text += chunk.text
        # Optional: Print chunks as they arrive if you still want to see the streaming
        # print(chunk.text, end="")

    # Now, full_response_text contains the complete JSON string
    #print("\n--- Complete Generated Output ---")
    #print(full_response_text)

    # You can return this string if you want to use it outside the function
    return full_response_text


def compare(torrent: str, subtitle: str) -> dict:
    generated_json_string = generate(
        torrent=torrent,
        subtitle=subtitle,
    )

    import json
    try:
        data = json.loads(generated_json_string)
        return data
    except json.JSONDecodeError as e:
        print(f"\nError decoding JSON: {e}")
        print(f"Raw string: {generated_json_string}")
