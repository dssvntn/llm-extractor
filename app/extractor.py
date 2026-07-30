import os

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.schemas import ExtractedDocument


SYSTEM_PROMPT = """
Ты извлекаешь данные из чеков, счетов и договоров.

Извлеки из документа следующие поля:

- date — дата и время документа;
- document_number — номер документа;
- total_amount — итоговая сумма;
- items — список товаров или услуг, содержащий название и цену.

Правила:

1. Не придумывай данные, которых нет в документе.
2. Если дата отсутствует, верни null.
3. Если номер документа отсутствует, верни null.
4. Если итоговая сумма отсутствует, верни null.
5. Если товаров или услуг нет, верни пустой список.
6. Не считай скидку, сдачу, НДС или отдельный платёж итоговой суммой.
7. Исправляй очевидные ошибки форматирования чисел:
   "142,00" → 142.00
   "289..99" → 289.99
   "45.50р" → 45.50
8. Игнорируй лишние символы, разрывы строк и другой очевидный мусор.
9. В список items включай только товары или услуги.
10. Не включай в items кассира, поставщика, заказчика,
    реквизиты и другие служебные данные.
11. Если значение невозможно определить достоверно,
    не угадывай его, а верни null.
"""


class ExtractorError(Exception):
    """Ошибка при извлечении данных из документа."""


class Extractor:
    """Извлекает структурированные данные из документа с помощью LLM."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash-lite",
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ExtractorError(
                "Не найден GEMINI_API_KEY."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def extract(self, text: str) -> ExtractedDocument:
        """Извлекает данные из текста документа."""

        if not text or not text.strip():
            raise ExtractorError("Передан пустой текст документа.")

        prompt = f"""
{SYSTEM_PROMPT}

Текст документа:

{text}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedDocument,
                ),
            )

            if not response.text:
                raise ExtractorError(
                    "Модель не вернула ответ."
                )

            return ExtractedDocument.model_validate_json(response.text)

        except ValidationError as exc:
            raise ExtractorError(
                "Ответ модели не соответствует Pydantic-схеме."
            ) from exc

        except ExtractorError:
            raise

        except Exception as exc:
            raise ExtractorError(
                f"Ошибка при обращении к Gemini API: {exc}"
            ) from exc
