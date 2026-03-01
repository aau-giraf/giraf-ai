import base64

import httpx

from core.exceptions import ProviderError
from core.ports import ImageGeneratorPort
from core.types import ImageGenerationRequest, ImageGenerationResult

_ASPECT_RATIO_MAP = {
    (512, 512): "1:1",
    (1024, 1024): "1:1",
    (1024, 768): "4:3",
    (768, 1024): "3:4",
    (1280, 720): "16:9",
    (720, 1280): "9:16",
}


class GeminiImageAdapter(ImageGeneratorPort):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-image") -> None:
        self._model = model
        self._client = httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com/v1beta",
            headers={"x-goog-api-key": api_key},
            timeout=60.0,
        )

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        aspect_ratio = _ASPECT_RATIO_MAP.get(request.size, "1:1")
        try:
            resp = await self._client.post(
                f"/models/{self._model}:generateContent",
                json={
                    "contents": [{"parts": [{"text": request.prompt}]}],
                    "generationConfig": {
                        "responseModalities": ["TEXT", "IMAGE"],
                        "imageConfig": {"aspectRatio": aspect_ratio},
                    },
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError("gemini", f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ProviderError("gemini", str(e)) from e

        data = resp.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            inline = next(p["inlineData"] for p in parts if "inlineData" in p)
        except (KeyError, IndexError, StopIteration) as e:
            raise ProviderError("gemini", "No image in response") from e

        image_bytes = base64.b64decode(inline["data"])
        mime = inline.get("mimeType", "image/png")
        fmt = mime.split("/")[-1] if "/" in mime else "png"

        return ImageGenerationResult(
            image_data=image_bytes,
            format=fmt,
            prompt_used=request.prompt,
            provider="gemini",
            metadata=request.metadata,
        )

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get(f"/models/{self._model}")
            return resp.status_code == 200
        except httpx.RequestError:
            return False
