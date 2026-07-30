from app.extractor import Extractor
from tests.data import CLEAN_DOCUMENT, EMPTY_DOCUMENT, NOISY_DOCUMENT


def test_clean_document():
    """Проверяет извлечение из чистого документа."""

    extractor = Extractor()
    result = extractor.extract(CLEAN_DOCUMENT)

    assert result.document_number == "0004592"
    assert result.total_amount == 667.49
    assert result.date is not None

    assert len(result.items) == 4

    assert result.items[0].name == 'Хлеб "Бородинский"'
    assert result.items[0].price == 45.50


def test_noisy_document():
    """Проверяет извлечение из зашумлённого документа."""

    extractor = Extractor()
    result = extractor.extract(NOISY_DOCUMENT)

    assert result.document_number == "0004592"
    assert result.total_amount == 667.49
    assert result.date is not None

    assert len(result.items) == 4

    prices = [item.price for item in result.items]

    assert 45.50 in prices
    assert 142.00 in prices
    assert 289.99 in prices
    assert 190.00 in prices


def test_document_without_data():
    """Проверяет документ без нужных данных."""

    extractor = Extractor()
    result = extractor.extract(EMPTY_DOCUMENT)

    assert result.date is None
    assert result.document_number is None
    assert result.total_amount is None
    assert result.items == []
