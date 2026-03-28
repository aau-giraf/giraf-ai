import httpx

from core.exceptions import ProviderError
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

        try:
            resp = await self._client.post("/v1/image/generate", json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError("imagegen", f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ProviderError("imagegen", str(e)) from e

        return ImageGenerationResult(
            image_data=resp.content,
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
