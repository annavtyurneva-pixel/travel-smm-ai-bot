from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from typing import Protocol

from app.services.prompt_loader import PromptLoader


class AIServiceError(RuntimeError):
    """Безопасная ошибка, которую можно показать пользователю."""


@dataclass(frozen=True, slots=True)
class ContentBrief:
    destination: str
    audience: str
    post_format: str
    tone: str
    goal: str
    topic: str = "на выбор редактора"


class LLMService(Protocol):
    async def generate_ideas(self, brief: ContentBrief) -> str: ...
    async def generate_post(self, brief: ContentBrief) -> str: ...
    async def generate_image_prompt(self, brief: ContentBrief, post: str) -> str: ...


class MockLLMService:
    """Предсказуемые ответы для демонстрации и тестов без API."""

    async def generate_ideas(self, brief: ContentBrief) -> str:
        return (
            f"1. Первый день в {brief.destination}\nОписание: маршрут без спешки для знакомства с местом.\n\n"
            "2. Что положить в ручную кладь\nОписание: практичный чек-лист для спокойной поездки.\n\n"
            "3. Районы с разным настроением\nОписание: сравнение вариантов прогулки под интересы читателя.\n\n"
            "4. День глазами местного жителя\nОписание: идеи неторопливого знакомства с культурой и бытом.\n\n"
            "5. Ошибки при планировании\nОписание: полезная памятка с советом перепроверять актуальные правила."
        )

    async def generate_post(self, brief: ContentBrief) -> str:
        return (
            f"{brief.destination}: путешествие, в котором есть место открытиям\n\n"
            f"Как увидеть новое место без гонки по списку достопримечательностей? "
            f"Для аудитории «{brief.audience}» лучше работает простой план: выбрать один район, "
            "оставить время на неспешную прогулку и заранее отметить несколько запасных точек.\n\n"
            f"Формат этой поездки — {brief.post_format.lower()}, а цель — {brief.goal.lower()}. "
            "Начните утро с прогулки, днём загляните на локальный рынок или в небольшой музей, "
            "а вечер оставьте свободным. Так маршрут сохранит структуру, но не превратится в марафон.\n\n"
            "Перед поездкой:\n• проверьте часы работы и правила на официальных сайтах;\n"
            "• сохраните офлайн-карту;\n• предусмотрите альтернативу на случай погоды;\n"
            "• уточните актуальные требования к въезду и безопасности.\n\n"
            f"Какой формат знакомства с {brief.destination} выбрали бы вы?\n\n"
            "#путешествия #тревелсоветы #маршрут #отдых"
        )

    async def generate_image_prompt(self, brief: ContentBrief, post: str) -> str:
        return (
            f"Квадратная редакционная тревел-иллюстрация: атмосферная улица в {brief.destination}, "
            f"настроение — {brief.tone.lower()}, естественный золотой свет, глубокая перспектива, "
            "чистая композиция, реалистичная фотографическая эстетика, без текста, логотипов, "
            "водяных знаков и узнаваемых публичных людей."
        )


class OpenAILLMService:
    def __init__(self, api_key: str, model: str, loader: PromptLoader | None = None) -> None:
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key, timeout=45.0, max_retries=2)
        self.model = model
        self.loader = loader or PromptLoader()

    async def _complete(self, prompt: str) -> str:
        try:
            response = await asyncio.wait_for(
                self.client.responses.create(model=self.model, input=prompt), timeout=60
            )
            text = response.output_text.strip()
        except Exception as exc:
            raise AIServiceError("Сервис генерации текста временно недоступен. Попробуйте ещё раз.") from exc
        if not text:
            raise AIServiceError("Модель вернула пустой ответ. Попробуйте изменить тему.")
        return text[:4000]

    async def generate_ideas(self, brief: ContentBrief) -> str:
        prompt = self.loader.render(
            "ideas", destination=brief.destination, audience=brief.audience,
            goal=brief.goal, tone=brief.tone
        )
        return await self._complete(prompt)

    async def generate_post(self, brief: ContentBrief) -> str:
        return await self._complete(self.loader.render("post", **asdict(brief)))

    async def generate_image_prompt(self, brief: ContentBrief, post: str) -> str:
        values = {**asdict(brief), "post_excerpt": post[:1200]}
        return await self._complete(self.loader.render("image", **values))


def build_llm_service(*, mock_mode: bool, api_key: str | None, model: str) -> LLMService:
    if mock_mode:
        return MockLLMService()
    if not api_key:
        raise AIServiceError("Для реального режима не задан OPENAI_API_KEY.")
    return OpenAILLMService(api_key, model)
