"""Unit tests for Polite Scraper parser and data models."""

from pathlib import Path
from urllib.parse import urljoin
import pytest
from pydantic import ValidationError

from src.models import BookRecord, RawBook
from src.parser import (
    extract_book_details,
    extract_catalogue_book_urls,
    extract_next_page_url,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_price_normalization():
    """Verify price string normalization to float in GBP."""
    raw = RawBook(
        title="Test Book",
        product_url="https://books.toscrape.com/catalogue/test_1/index.html",
        price_text="£51.77",
        availability_text="In stock (22 available)",
        rating_text="Three",
        description="A great book",
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-11-17T12:00:00Z",
    )
    validated = BookRecord.from_raw(raw)
    assert validated.price_gbp == 51.77
    assert isinstance(validated.price_gbp, float)
    assert validated.price_text == "£51.77"


def test_relative_to_absolute_urls():
    """Verify relative URLs are converted to valid absolute URLs."""
    base_url = "https://books.toscrape.com/catalogue/page-1.html"
    relative_book = "../book-slug_100/index.html"
    absolute_book = urljoin(base_url, relative_book)
    assert absolute_book == "https://books.toscrape.com/book-slug_100/index.html"

    # Test extract_next_page_url with sample html
    html = '<ul class="pager"><li class="next"><a href="page-2.html">next</a></li></ul>'
    next_url = extract_next_page_url(html, base_url)
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_missing_description_stored_as_none():
    """Verify books lacking a description store None rather than invented text."""
    fixture_path = FIXTURES_DIR / "missing_desc.html"
    content = fixture_path.read_text(encoding="utf-8")
    product_url = "https://books.toscrape.com/catalogue/no-desc_1/index.html"
    source_page = "https://books.toscrape.com/catalogue/page-1.html"

    raw = extract_book_details(content, product_url, source_page, "2026-11-17T12:00:00Z")
    assert raw.description is None

    validated = BookRecord.from_raw(raw)
    assert validated.description is None
    assert validated.title == "Book Without Description"
    assert validated.price_gbp == 19.99


def test_extra_whitespace_handling():
    """Verify parser strips excessive whitespace correctly."""
    fixture_path = FIXTURES_DIR / "extra_whitespace.html"
    content = fixture_path.read_text(encoding="utf-8")
    product_url = "https://books.toscrape.com/catalogue/whitespace_1/index.html"
    source_page = "https://books.toscrape.com/catalogue/page-1.html"

    raw = extract_book_details(content, product_url, source_page, "2026-11-17T12:00:00Z")
    validated = BookRecord.from_raw(raw)

    assert validated.title == "Book With Extra Whitespace"
    assert validated.price_gbp == 42.50
    assert validated.rating_text == "Five"
    assert "trailing and leading whitespace" in validated.description
    assert not validated.description.startswith(" ")


def test_duplicate_url_deduplication():
    """Verify that multiple occurrences of the same book URL produce a single record."""
    urls = [
        "https://books.toscrape.com/catalogue/book1_1/index.html",
        "https://books.toscrape.com/catalogue/book2_2/index.html",
        "https://books.toscrape.com/catalogue/book1_1/index.html",
    ]
    unique = list(dict.fromkeys(urls))
    assert len(unique) == 2
    assert unique == [
        "https://books.toscrape.com/catalogue/book1_1/index.html",
        "https://books.toscrape.com/catalogue/book2_2/index.html",
    ]


def test_malformed_html_fixture_does_not_crash():
    """Verify malformed HTML without standard product container does not crash parser."""
    fixture_path = FIXTURES_DIR / "malformed.html"
    content = fixture_path.read_text(encoding="utf-8")
    product_url = "https://books.toscrape.com/catalogue/malformed_1/index.html"
    source_page = "https://books.toscrape.com/catalogue/page-1.html"

    raw = extract_book_details(content, product_url, source_page, "2026-11-17T12:00:00Z")
    assert raw.title == "Untitled"
    assert raw.price_text == ""
    assert raw.description is None


def test_schema_validation_rejects_invalid_urls():
    """Verify schema rejects non-https URLs."""
    raw = RawBook(
        title="Bad URL Book",
        product_url="http://insecure.com/book",
        price_text="£10.00",
        availability_text="In stock",
        rating_text="One",
        description=None,
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-11-17T12:00:00Z",
    )
    with pytest.raises(ValidationError):
        BookRecord.from_raw(raw)
