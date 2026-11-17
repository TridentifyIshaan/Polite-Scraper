"""Unit tests for export utilities (CSV, change detection, dashboard)."""

import json
from pathlib import Path

from src.export import (
    compute_change_detection,
    export_books_to_csv,
    generate_dashboard,
)
from src.models import BookRecord, RunReport


def create_sample_record(title: str = "Sample", price: float = 25.0, desc: str = "Desc") -> BookRecord:
    return BookRecord(
        title=title,
        product_url=f"https://books.toscrape.com/catalogue/{title.lower()}/index.html",
        price_text=f"£{price:.2f}",
        price_gbp=price,
        availability_text="In stock (5 available)",
        rating_text="Three",
        description=desc,
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-11-17T12:00:00Z",
    )


def test_export_books_to_csv(tmp_path: Path):
    records = [create_sample_record("Book A", 10.0), create_sample_record("Book B", 20.0)]
    csv_file = tmp_path / "books.csv"
    export_books_to_csv(records, csv_file)

    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8")
    lines = content.strip().splitlines()
    assert len(lines) == 3  # Header + 2 rows
    assert "title,product_url,price_gbp" in lines[0]
    assert "Book A" in lines[1]
    assert "10.0" in lines[1]


def test_change_detection_workflow(tmp_path: Path):
    hash_file = tmp_path / "hashes.json"
    records_initial = [create_sample_record("Book 1", 10.0), create_sample_record("Book 2", 20.0)]

    # Initial run: all new
    r1 = compute_change_detection(records_initial, hash_file)
    assert r1["new"] == 2
    assert r1["changed"] == 0
    assert r1["unchanged"] == 0
    assert r1["gone"] == 0

    # Second run with same records: all unchanged
    r2 = compute_change_detection(records_initial, hash_file)
    assert r2["new"] == 0
    assert r2["changed"] == 0
    assert r2["unchanged"] == 2
    assert r2["gone"] == 0

    # Third run with one changed and one new, one gone
    records_mod = [
        create_sample_record("Book 1", 15.0),  # price changed
        create_sample_record("Book 3", 30.0),  # new book (Book 2 gone)
    ]
    r3 = compute_change_detection(records_mod, hash_file)
    assert r3["new"] == 1
    assert r3["changed"] == 1
    assert r3["unchanged"] == 0
    assert r3["gone"] == 1


def test_generate_dashboard(tmp_path: Path):
    records = [create_sample_record("Dashboard Test", 35.50)]
    report = RunReport(
        start_time="2026-11-17T12:00:00Z",
        duration_seconds=1.23,
        pages_fetched=1,
        cache_hits=2,
        valid_records=1,
        invalid_records=0,
        failed_pages=0,
    )
    dash_file = tmp_path / "dashboard.html"
    generate_dashboard(records, report, dash_file)

    assert dash_file.exists()
    html = dash_file.read_text(encoding="utf-8")
    assert "The Polite Scraper · Dashboard" in html
    assert "Dashboard Test" in html
    assert "£35.50" in html
