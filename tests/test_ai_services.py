import pytest
import struct

from app.services.image_service import MockImageService
from app.services.llm_service import ContentBrief, MockLLMService, build_llm_service
from app.services.prompt_loader import PromptError, PromptLoader


@pytest.fixture
def brief():
    return ContentBrief(
        destination="Калининград", audience="самостоятельные путешественники",
        post_format="полезный гид", tone="дружелюбный", goal="сохранения",
        topic="маршрут на выходные",
    )


def test_all_prompt_files_render(brief):
    loader = PromptLoader()
    common = {
        "destination": brief.destination, "audience": brief.audience,
        "post_format": brief.post_format, "tone": brief.tone,
        "goal": brief.goal, "topic": brief.topic, "post_excerpt": "Тестовый пост",
    }
    for name in ("ideas", "post", "image"):
        assert len(loader.render(name, **common)) > 200


def test_missing_prompt_field_has_clear_error(tmp_path):
    (tmp_path / "x_prompt.txt").write_text("{missing}", encoding="utf-8")
    with pytest.raises(PromptError, match="missing"):
        PromptLoader(tmp_path).render("x")


@pytest.mark.asyncio
async def test_mock_ideas_contains_five_items(brief):
    result = await MockLLMService().generate_ideas(brief)
    assert all(f"{number}." in result for number in range(1, 6))


@pytest.mark.asyncio
async def test_mock_post_uses_brief_and_has_hashtags(brief):
    result = await MockLLMService().generate_post(brief)
    assert brief.destination in result
    assert brief.audience in result
    assert "#путешествия" in result


@pytest.mark.asyncio
async def test_mock_image_is_png(brief):
    prompt = await MockLLMService().generate_image_prompt(brief, "Пост")
    image = await MockImageService().generate(prompt)
    assert image.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", image[16:24])
    assert (width, height) == (512, 512)


def test_factory_selects_mock_without_key():
    assert isinstance(build_llm_service(mock_mode=True, api_key=None, model="test"), MockLLMService)
