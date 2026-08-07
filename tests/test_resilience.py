from types import SimpleNamespace

import pytest

from app.services.llm_service import AIServiceError, OpenAILLMService


class FakeResponses:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error

    async def create(self, **kwargs):
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=self.output)


def service_with(response):
    service = object.__new__(OpenAILLMService)
    service.client = SimpleNamespace(responses=response)
    service.model = "test"
    return service


@pytest.mark.asyncio
async def test_empty_llm_response_has_clear_error():
    with pytest.raises(AIServiceError, match="пустой ответ"):
        await service_with(FakeResponses("   "))._complete("prompt")


@pytest.mark.asyncio
async def test_api_failure_does_not_leak_details():
    with pytest.raises(AIServiceError, match="временно недоступен") as caught:
        await service_with(FakeResponses(error=RuntimeError("SECRET_INTERNAL_DETAIL")))._complete("prompt")
    assert "SECRET_INTERNAL_DETAIL" not in str(caught.value)


@pytest.mark.asyncio
async def test_llm_response_is_bounded_for_telegram():
    result = await service_with(FakeResponses("x" * 6000))._complete("prompt")
    assert len(result) == 4000

