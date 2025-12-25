"""API client for vision analysis."""

import requests
from vision_mcp.exceptions import VisionRequestError


class OpenAICompatibleClient:
    """Client for making requests to OpenAI-compatible APIs."""

    def __init__(self, api_key: str, api_base: str, model: str):
        """Initialize the API client.

        Args:
            api_key: The API key for authentication
            api_base: The API base URL
            model: The model to use for vision tasks
        """
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def analyze_image(self, prompt: str, image_data_url: str) -> str:
        """Analyze an image using the Vision API.

        Args:
            prompt: The text prompt describing what to analyze
            image_data_url: The image as a data URL (data:image/...;base64,...)

        Returns:
            The model's response text

        Raises:
            VisionRequestError: If the request fails
        """
        url = f"{self.api_base}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }]
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise VisionRequestError(f"Request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise VisionRequestError(f"Invalid response format: {str(e)}")
