import os

from openai import APIError, OpenAI
from pydantic import ValidationError

from app.schemas import ExtractedDocument


SYSTEM_PROMPT = """
Ты извлекаешь структурированные данные из документов:
чеков, счетов и договоров.

Твоя задача — извлечь из переданного текста следующие сущности:

1. date — дата и время документа.
2. document_number — номер документа.
3. total_amount — итоговая сумма документа.
4. items — список товаров или услуг, для каждого указать:
   - name — название;
   - price — цена.

Правила:

1. Не придумывай значения, которых нет в исходном тексте.
2. Если дата отсутствует или определить её невозможно, верни null.
3. Если номер документа отсутствует или определить его невозможно,
   верни null.
4. Если итоговая сумма отсутствует или определить её невозможно,
   верни null.
5. Если товары или услуги отсутствуют, верни пустой список.
6. Не считай скидку, сдачу, НДС, аванс или отдельный платёж
   итоговой суммой, если они явно не обозначены как итоговая сумма.
7. Учитывай очевидные ошибки распознавания текста (OCR) и форматирования.
   Например:
   - "142,00" следует интерпретировать как 142.00;
   - "289..99" следует интерпретировать как 289.99;
   - "45.50р" следует интерпретировать как 45.50.
8. Игнорируй декоративные символы, лишние пробелы, разрывы строк,
   штрих-коды и прочий мусор, если он не содержит полезной информации.
9. В items включай только товары или услуги.
10. Не включай в items поставщиков, заказчиков, кассиров,
    реквизиты, номера транзакций и другие данные,
    которые не являются товарами или услугами.
11. Если в документе указано несколько платежей или этапов оплаты,
    не суммируй их самостоятельно. Извлекай только явно указанную
    итоговую стоимость документа.
12. Если информация неоднозначна, не делай предположений.
    Лучше вернуть null или пустой список.
"""


class ExtractorError(Exception):
    """Базовая ошибка сервиса извлечения данных."""


class Extractor:
    """Извлекает структурированные данные из текста документа с помощью LLM."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-5-mini",
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ExtractorError(
                "Не найден API ключ OpenAI. "
                "Укажите OPENAI_API_KEY в переменных окружения."
            )

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def extract(self, text: str) -> ExtractedDocument:
        """
        Извлекает данные из переданного текста документа.

        Args:
            text: Исходный текст документа.

        Returns:
            Валидированный объект ExtractedDocument.

        Raises:
            ExtractorError: Если входной текст пустой или произошла
                ошибка при обращении к API/валидации ответа.
        """

        if not text or not text.strip():
            raise ExtractorError("Передан пустой текст документа.")

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "developer",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                text_format=ExtractedDocument,
            )

            result = response.output_parsed

            if result is None:
                raise ExtractorError(
                    "Модель не вернула структурированный ответ."
                )

            return result

        except ValidationError as exc:
            raise ExtractorError(
                "Ответ модели не прошёл валидацию Pydantic."
            ) from exc

        except APIError as exc:
            raise ExtractorError(
                f"Ошибка OpenAI API: {exc}"
            ) from exc
