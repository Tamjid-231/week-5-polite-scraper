"""Schema and normalization for scraped book records."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Literal, Mapping

from pydantic import BaseModel, Field, HttpUrl, field_validator


PRICE_PATTERN = re.compile(r"^£(\d+(?:\.\d{2})?)$")


class BookRecord(BaseModel):
    title: str = Field(min_length=1)
    product_url: HttpUrl
    price_text: str = Field(min_length=1)
    price_gbp: float = Field(ge=0)
    availability_text: str = Field(min_length=1)
    rating_text: Literal["One", "Two", "Three", "Four", "Five"]
    description: str | None
    source_page: HttpUrl
    fetched_at: datetime

    @field_validator("product_url", "source_page")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("URL must use https")
        return value


def normalize_price(price_text: str) -> float:
    cleaned = price_text.strip()
    match = PRICE_PATTERN.fullmatch(cleaned)
    if match is None:
        raise ValueError(f"invalid GBP price: {price_text!r}")
    return float(match.group(1))


def validate_record(raw: Mapping[str, object]) -> BookRecord:
    values = dict(raw)
    values["price_gbp"] = normalize_price(str(values.get("price_text", "")))
    return BookRecord.model_validate(values)

