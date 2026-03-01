import io
from dataclasses import replace
from pathlib import Path

from PIL import Image

from core.ports import ImageGeneratorPort
from core.types import ImageGenerationRequest, ImageGenerationResult

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "image"


def _load_style_prompts() -> dict[str, str]:
    prompts: dict[str, str] = {}
    if _PROMPTS_DIR.is_dir():
        for f in _PROMPTS_DIR.glob("*.md"):
            prompts[f.stem] = f.read_text().strip()
    return prompts


class ImageService:
    def __init__(self, adapter: ImageGeneratorPort) -> None:
        self.adapter = adapter
        self._style_prompts = _load_style_prompts()

    async def health_check(self) -> bool:
        return await self.adapter.health_check()

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        enriched = self._build_prompt(request)
        result = await self.adapter.generate(enriched)
        return self._post_process(result, request)

    def _build_prompt(self, request: ImageGenerationRequest) -> ImageGenerationRequest:
        template = self._style_prompts.get(request.style, "{prompt}")
        enriched_prompt = template.format(prompt=request.prompt)
        return replace(request, prompt=enriched_prompt)

    def _post_process(
        self, result: ImageGenerationResult, request: ImageGenerationRequest
    ) -> ImageGenerationResult:
        if result.format == request.format:
            img = Image.open(io.BytesIO(result.image_data))
            if img.size != request.size:
                resized = img.resize(request.size, Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                pil_fmt = "PNG" if request.format == "png" else "WEBP"
                resized.save(buf, format=pil_fmt)
                return replace(result, image_data=buf.getvalue())
        return result
