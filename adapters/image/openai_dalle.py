import base64

import httpx

from core.exceptions import ProviderError
from core.ports import ImageGeneratorPort
from core.types import ImageGenerationRequest, ImageGenerationResult

_SIZE_MAP = {
    (256, 256): "256x256",
    (512, 512): "512x512",
    (1024, 1024): "1024x1024",
}


class OpenAIDalleAdapter(ImageGeneratorPort):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        size_str = _SIZE_MAP.get(request.size, "512x512")
        try:
            resp = await self._client.post(
                "/images/generations",
                json={
                    "model": "dall-e-3",
                    "prompt": request.prompt,
                    "n": 1,
                    "size": size_str,
                    "response_format": "b64_json",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError("openai_dalle", f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ProviderError("openai_dalle", str(e)) from e

        data = resp.json()
        try:
            image_b64 = data["data"][0]["b64_json"]
        except (KeyError, IndexError) as e:
            raise ProviderError("openai_dalle", "No image in response") from e
        image_bytes = base64.b64decode(image_b64)

        return ImageGenerationResult(
            image_data=image_bytes,
            format="png",
            prompt_used=request.prompt,
            provider="openai_dalle",
            metadata=request.metadata,
        )

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/models")
            return resp.status_code == 200
        except httpx.RequestError:
            return False
