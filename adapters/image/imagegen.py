import httpx

from core.http import provider_request
from core.ports import ImageGeneratorPort
from core.types import ImageGenerationRequest, ImageGenerationResult


class ImagegenAdapter(ImageGeneratorPort):
    """Image adapter for giraf-imagegen running on a local GPU server."""

    def __init__(self, base_url: str = "http://localhost:8300") -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=120.0,  # Image generation can be slow
        )

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        body = {
            "prompt": request.prompt,
            "width": request.size[0],
            "height": request.size[1],
            "format": request.format,
        }

        async with provider_request(
            self._client, "post", "/v1/image/generate", "imagegen", json=body
        ) as resp:
            content = resp.content

        return ImageGenerationResult(
            image_data=content,
            format=request.format,
            prompt_used=request.prompt,
            provider="imagegen",
            metadata=request.metadata,
        )

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/health")
            return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def close(self) -> None:
        await self._client.aclose()
