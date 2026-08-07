from __future__ import annotations

from pathlib import Path


class PromptError(ValueError):
    pass


class PromptLoader:
    def __init__(self, directory: str | Path = "prompts") -> None:
        self.directory = Path(directory)

    def render(self, name: str, **values: str) -> str:
        path = self.directory / f"{name}_prompt.txt"
        if not path.is_file():
            raise PromptError(f"Файл промпта не найден: {path}")
        template = path.read_text(encoding="utf-8").strip()
        try:
            result = template.format(**values).strip()
        except KeyError as exc:
            raise PromptError(f"Не заполнено поле промпта: {exc.args[0]}") from exc
        if not result:
            raise PromptError(f"Промпт {name} пуст.")
        return result

