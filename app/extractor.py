import json
import os

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from app.schemas import ExtractedDocument


load_dotenv()


class ExtractorError(Exception):
    """Ошибка извлечения данных из документа."""


class Extractor:
    """Извлекает структурированные данные из текста документа с помощью LLM."""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "openrouter/free"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ExtractorError(
                "Не найден OPENROUTER_API_KEY."
            )

    def extract(self, text: str) -> ExtractedDocument:
        """Извлекает данные из переданного текста."""

        if not text.strip():
            raise ExtractorError("Передан пустой текст.")

        try:
            response = httpx.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._build_system_prompt(),
                        },
                        {
                            "role": "user",
                            "content": text,
                        },
                    ],
                    "temperature": 0,
                    "response_format": {
                        "type": "json_object",
                    },
                },
                timeout=60,
            )

            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise ExtractorError(
                f"OpenRouter API вернул ошибку "
                f"{exc.response.status_code}: {exc.response.text}"
            ) from exc

        except httpx.RequestError as exc:
            raise ExtractorError(
                f"Ошибка соединения с OpenRouter API: {exc}"
            ) from exc

        try:
            data = response.json()

            content = data["choices"][0]["message"]["content"]

        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ExtractorError(
                "OpenRouter вернул неожиданный формат ответа."
            ) from exc

        if not content or not content.strip():
            raise ExtractorError(
                "LLM вернула пустой ответ."
            )

        try:
            result = json.loads(content)

        except json.JSONDecodeError as exc:
            raise ExtractorError(
                "LLM вернула некорректный JSON."
            ) from exc

        try:
            return ExtractedDocument.model_validate(result)

        except ValidationError as exc:
            raise ExtractorError(
                "Ответ LLM не соответствует Pydantic-схеме."
            ) from exc

    @staticmethod
    def _build_system_prompt() -> str:
        schema = json.dumps(
            ExtractedDocument.model_json_schema(),
            ensure_ascii=False,
            indent=2,
        )

        return f"""
Ты извлекаешь структурированные данные из текста документов.

Нужно извлечь:
- дату документа;
- номер документа;
- итоговую сумму;
- список товаров или услуг с названием и ценой.

Правила:

1. Не придумывай данные, которых нет в исходном тексте.

2. Если дата отсутствует, верни null.

3. Если номер документа отсутствует, верни null.

4. Если итоговая сумма отсутствует, верни null.

5. Если товаров или услуг нет, верни пустой список.

6. Исправляй очевидные опечатки и шум в тексте,
   если смысл однозначно понятен.

7. Суммы и цены возвращай числами без обозначения валюты.

8. Даты в формате DD/MM/YYYY интерпретируй как
   день/месяц/год.

9. Например:
   12/05/2023 означает 12 мая 2023 года,
   а не 5 декабря 2023 года.

10. Если время указано, сохрани его.

11. Если время отсутствует, не придумывай его.

12. Дату возвращай в формате ISO 8601.

13. Верни только JSON.

14. Не добавляй Markdown, комментарии,
    пояснения или любой другой текст.

Ответ должен соответствовать следующей Pydantic JSON Schema:

{schema}
"""
