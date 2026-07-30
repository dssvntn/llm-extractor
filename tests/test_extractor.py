from app.extractor import Extractor


CLEAN_TEXT = """
ЧЕК № 0004592
Дата: 12/05/2023 14:22

ПРОДУКТЫ:
Хлеб "Бородинский" — 45.50 руб.
Молоко 3.2% — 142.00 руб.
Сыр Пармезан — 289.99 руб.
Масло сливочное 82.5% — 190.00 руб.

ИТОГО: 667.49 руб.
"""


NOISY_TEXT = """
*** ЧЕK № 0004592 ***
Дaта: 12/05/2023 14:22
--------------------------

ПРОДУКТЫ!!!

Хлeб "Бородинский" х 1 шт.     45.50р
Молоко 3.2% (пак) х 2 шт.      142,00!!!
Сыр Пармезан (нарезка) - 0.15кг  289..99
Масло сл. 82.5% х 1 шт.        190р

--------------------------
ИТОГО: 667.49 руб.
Скидка по карте: 5.00
Сдача: 33.00

[|||| || | ||| | || |||]
"""


EMPTY_TEXT = """
Кассовый терминал
--------------------------------
Кассир: Иванова А.А.
Спасибо за покупку!
--------------------------------
"""


def test_clean_document():
    extractor = Extractor()

    result = extractor.extract(CLEAN_TEXT)

    assert result.document_number == "0004592"
    assert result.date is not None
    assert result.date.year == 2023
    assert result.date.month == 5
    assert result.date.day == 12
    assert result.total_amount == 667.49
    assert len(result.items) == 4


def test_noisy_document():
    extractor = Extractor()

    result = extractor.extract(NOISY_TEXT)

    assert result.document_number == "0004592"
    assert result.date is not None
    assert result.date.year == 2023
    assert result.date.month == 5
    assert result.date.day == 12
    assert result.total_amount == 667.49
    assert len(result.items) == 4


def test_document_without_data():
    extractor = Extractor()

    result = extractor.extract(EMPTY_TEXT)

    assert result.document_number is None
    assert result.date is None
    assert result.total_amount is None
    assert result.items == []
