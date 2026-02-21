import io
from dataclasses import replace

from PIL import Image

from core.ports import ImageGeneratorPort
from core.types import ImageGenerationRequest, ImageGenerationResult

STYLE_PROMPTS = {
    "pictogram": (
        "A simple, flat, colorful pictogram icon of {prompt}. "
        "White background, no text, suitable for children with autism."
    ),
    "realistic": "A photorealistic image of {prompt}.",
    "cartoon": "A friendly cartoon illustration of {prompt}, suitable for children.",
}


class ImageService:
    def __init__(self, adapter: ImageGeneratorPort) -> None:
        self.adapter = adapter

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        enriched = self._build_prompt(request)
        result = await self.adapter.generate(enriched)
        return self._post_process(result, request)

    def _build_prompt(self, request: ImageGenerationRequest) -> ImageGenerationRequest:
        template = STYLE_PROMPTS.get(request.style, "{prompt}")
        enriched_prompt = template.format(prompt=request.prompt)
        return replace(request, prompt=enriched_prompt)

    def _post_process(
        self, result: ImageGenerationResult, request: ImageGenerationRequest
    ) -> ImageGenerationResult:
        if result.format == request.format:
            img = Image.open(io.BytesIO(result.image_data))
            if img.size != request.size:
                img = img.resize(request.size, Image.LANCZOS)
                buf = io.BytesIO()
                pil_fmt = "PNG" if request.format == "png" else "WEBP"
                img.save(buf, format=pil_fmt)
                return replace(result, image_data=buf.getvalue())
        return result
