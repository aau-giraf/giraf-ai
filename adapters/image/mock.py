import io

from PIL import Image, ImageDraw

from core.ports import ImageGeneratorPort
from core.types import ImageGenerationRequest, ImageGenerationResult


class MockImageAdapter(ImageGeneratorPort):
    """Returns a colored placeholder image. For dev/test only."""

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        img = Image.new("RGB", request.size, color=(200, 220, 255))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"Mock: {request.prompt[:40]}", fill=(0, 0, 0))

        buf = io.BytesIO()
        pil_format = "PNG" if request.format == "png" else "WEBP"
        img.save(buf, format=pil_format)

        return ImageGenerationResult(
            image_data=buf.getvalue(),
            format=request.format,
            prompt_used=request.prompt,
            provider="mock",
            metadata=request.metadata,
        )

    async def health_check(self) -> bool:
        return True
