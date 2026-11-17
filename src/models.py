"""Pydantic schemas for Polite Scraper raw and normalized records."""

import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class RawBook(BaseModel):
    """Raw record extracted directly from book HTML."""
    title: str
    product_url: str
    price_text: str
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str


class BookRecord(BaseModel):
    """Normalized, schema-validated book record."""
    title: str = Field(..., min_length=1, description="Book title")
    product_url: str = Field(..., description="Canonical absolute product URL")
    price_text: str = Field(..., description="Original price text with currency symbol")
    price_gbp: float = Field(..., ge=0.0, description="Normalized price in GBP")
    availability_text: str = Field(..., min_length=1, description="Raw stock availability string")
    rating_text: str = Field(..., min_length=1, description="Book rating text (e.g. One, Two, Three)")
    description: Optional[str] = Field(default=None, description="Book description or null")
    source_page: str = Field(..., description="Provenance catalogue page URL")
    fetched_at: str = Field(..., description="ISO 8601 UTC fetch timestamp")

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(f"URL must start with https://, got: {v}")
        return v

    @classmethod
    def from_raw(cls, raw: RawBook) -> "BookRecord":
        """Convert a RawBook into a normalized BookRecord."""
        # Normalize price_text -> price_gbp
        clean_price_match = re.search(r"(\d+(?:\.\d+)?)", raw.price_text)
        if not clean_price_match:
            raise ValueError(f"Could not parse numeric price from: {raw.price_text}")
        price_gbp = round(float(clean_price_match.group(1)), 2)

        return cls(
            title=raw.title.strip(),
            product_url=raw.product_url.strip(),
            price_text=raw.price_text.strip(),
            price_gbp=price_gbp,
            availability_text=raw.availability_text.strip(),
            rating_text=raw.rating_text.strip(),
            description=raw.description.strip() if raw.description else None,
            source_page=raw.source_page.strip(),
            fetched_at=raw.fetched_at.strip(),
        )


class RunReport(BaseModel):
    """Run summary report."""
    start_time: str
    duration_seconds: float
    pages_fetched: int
    cache_hits: int
    valid_records: int
    invalid_records: int
    failed_pages: int
