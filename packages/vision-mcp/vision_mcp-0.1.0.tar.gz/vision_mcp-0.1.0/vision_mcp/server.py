"""
Vision MCP Server

MCP server for image analysis using Vision Language Models.
"""

import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from vision_mcp.utils import process_image_url
from vision_mcp.const import *
from vision_mcp.exceptions import VisionAPIError, VisionRequestError
from vision_mcp.client import OpenAICompatibleClient

load_dotenv()
fastmcp_log_level = os.getenv(ENV_FASTMCP_LOG_LEVEL) or "WARNING"

openai_api_key = os.getenv(ENV_OPENAI_API_KEY)
openai_api_base = os.getenv(ENV_OPENAI_API_BASE)
openai_model = os.getenv(ENV_OPENAI_MODEL)

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not openai_api_base:
    raise ValueError("OPENAI_API_BASE environment variable is required")
if not openai_model:
    raise ValueError("OPENAI_MODEL environment variable is required")

mcp = FastMCP("Vision", log_level=fastmcp_log_level)
openai_client = OpenAICompatibleClient(openai_api_key, openai_api_base, openai_model)


@mcp.tool(
    description="""

    A powerful LLM that can analyze and understand image content from files or URLs, follow your instruction.
    Use this tool to analyze images by LLM.
    Only support jpeg, png, webp formats. Other formats like pdf/gif/psd/svg and so on are not supported.

    Args:
        prompt (str): The text prompt describing what you want to analyze or extract from the image.
        image_source (str): The source location of the image to analyze.
            Accepts:
            - HTTP/HTTPS URL: "https://example.com/image.jpg"
            - Local file path:
                - Relative path: "images/photo.png"
                - Absolute path: "/Users/username/Documents/image.jpg"
            IMPORTANT: If the file path starts with @ symbol, you MUST remove the @ prefix before passing to this function.
            For example:
                - If you see "@Documents/photo.jpg", use "Documents/photo.jpg"
                - If you see "@/Users/username/image.png", use "/Users/username/image.png"
            Supported formats: JPEG, PNG, WebP

    Returns:
        Text content with the image analysis result.
    """
)
def analyze_image(
    prompt: str,
    image_source: str,
) -> TextContent:
    try:
        if not prompt:
            raise VisionRequestError("Prompt is required")
        if not image_source:
            raise VisionRequestError("Image source is required")

        processed_image_url = process_image_url(image_source)
        content = openai_client.analyze_image(prompt, processed_image_url)

        if not content:
            raise VisionRequestError("No content returned from VLM API")

        return TextContent(
            type="text",
            text=content
        )

    except VisionAPIError as e:
        return TextContent(
            type="text",
            text=f"Failed to analyze image: {str(e)}"
        )


def main():
    print("Starting Vision MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
