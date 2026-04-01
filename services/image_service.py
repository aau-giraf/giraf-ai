import io
import re
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
        return self._ensure_size(result, request.size)

    def _build_prompt(self, request: ImageGenerationRequest) -> ImageGenerationRequest:
        template = self._style_prompts.get(request.style, "{prompt}")
        sanitized = re.sub(r"[\n\r\t\x00-\x1f]", " ", request.prompt).strip()
        enriched_prompt = template.replace("{prompt}", sanitized)
        return replace(request, prompt=enriched_prompt)

    def _ensure_size(
        self, result: ImageGenerationResult, target_size: tuple[int, int]
    ) -> ImageGenerationResult:
        """Resize the generated image to match the requested dimensions."""
        img = Image.open(io.BytesIO(result.image_data))
        if img.size == target_size:
            return result
        resized = img.resize(target_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        pil_fmt = {"png": "PNG", "webp": "WEBP"}.get(result.format, result.format.upper())
        resized.save(buf, format=pil_fmt)
        return replace(result, image_data=buf.getvalue())
