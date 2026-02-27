import pytest

from adapters.image.mock import MockImageAdapter
from core.types import ImageGenerationRequest
from services.image_service import ImageService


@pytest.fixture
def image_service() -> ImageService:
    return ImageService(MockImageAdapter())


async def test_generate_returns_image(image_service: ImageService) -> None:
    req = ImageGenerationRequest(prompt="lasagna")
    result = await image_service.generate(req)
    assert result.image_data
    assert result.format == "png"
    assert result.provider == "mock"
    assert "pictogram" in result.prompt_used.lower()


async def test_prompt_enrichment_pictogram(image_service: ImageService) -> None:
    req = ImageGenerationRequest(prompt="apple", style="pictogram")
    enriched = image_service._build_prompt(req)
    assert "simple" in enriched.prompt.lower()
    assert "apple" in enriched.prompt


async def test_prompt_enrichment_realistic(image_service: ImageService) -> None:
    req = ImageGenerationRequest(prompt="cat", style="realistic")
    enriched = image_service._build_prompt(req)
    assert "photorealistic" in enriched.prompt.lower()


async def test_unknown_style_passes_through(image_service: ImageService) -> None:
    req = ImageGenerationRequest(prompt="dog", style="unknown_style")
    enriched = image_service._build_prompt(req)
    assert enriched.prompt == "dog"
