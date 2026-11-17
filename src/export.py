"""Export utilities: CSV export, change detection, and HTML observability dashboard."""

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from src.models import BookRecord, RunReport


def export_books_to_csv(records: List[BookRecord], output_path: Path) -> Path:
    """Export validated book records to CSV.
    
    Flattens newlines in descriptions and formats numeric price_gbp cleanly.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "title",
        "product_url",
        "price_gbp",
        "price_text",
        "availability_text",
        "rating_text",
        "description",
        "source_page",
        "fetched_at",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for rec in records:
            data = rec.model_dump()
            # Flatten multiline descriptions for clean tabular display
            if data["description"]:
                data["description"] = " ".join(data["description"].split())
            writer.writerow(data)

    return output_path


def compute_change_detection(
    records: List[BookRecord],
    hash_store_path: Path,
) -> Dict[str, Any]:
    """Detect new, changed, unchanged, or gone books since previous run."""
    current_hashes: Dict[str, str] = {}
    for r in records:
        content_repr = f"{r.title}|{r.price_gbp}|{r.availability_text}|{r.rating_text}|{r.description}"
        current_hashes[r.product_url] = hashlib.sha256(content_repr.encode("utf-8")).hexdigest()

    previous_hashes: Dict[str, str] = {}
    if hash_store_path.exists():
        try:
            previous_hashes = json.loads(hash_store_path.read_text(encoding="utf-8"))
        except Exception:
            previous_hashes = {}

    new_urls = [url for url in current_hashes if url not in previous_hashes]
    gone_urls = [url for url in previous_hashes if url not in current_hashes]
    changed_urls = [
        url for url in current_hashes
        if url in previous_hashes and current_hashes[url] != previous_hashes[url]
    ]
    unchanged_urls = [
        url for url in current_hashes
        if url in previous_hashes and current_hashes[url] == previous_hashes[url]
    ]

    report = {
        "new": len(new_urls),
        "changed": len(changed_urls),
        "unchanged": len(unchanged_urls),
        "gone": len(gone_urls),
        "total_current": len(records),
    }

    # Save current hashes for subsequent runs
    hash_store_path.write_text(json.dumps(current_hashes, indent=2), encoding="utf-8")
    return report


def generate_dashboard(
    records: List[BookRecord],
    report: RunReport,
    output_path: Path,
) -> Path:
    """Generate a lightweight, self-contained HTML observability dashboard."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prices = [r.price_gbp for r in records]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else 0.0
    avg_price = (sum(prices) / len(prices)) if prices else 0.0

    # Build rows HTML
    rows_html = []
    for r in records:
        desc_snippet = (r.description[:75] + "...") if r.description else "<em>None</em>"
        rows_html.append(
            f"<tr>"
            f"<td><strong>{r.title}</strong></td>"
            f"<td>£{r.price_gbp:.2f}</td>"
            f"<td><span class='badge'>{r.rating_text}</span></td>"
            f"<td>{r.availability_text}</td>"
            f"<td><a href='{r.product_url}' target='_blank'>View</a></td>"
            f"<td>{desc_snippet}</td>"
            f"</tr>"
        )
    rows_str = "\n".join(rows_html)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Polite Scraper Dashboard</title>
  <style>
    :root {{
      --bg: #0d1117; --card: #161b22; --border: #30363d;
      --text: #c9d1d9; --accent: #2ea043; --blue: #58a6ff;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg); color: var(--text); margin: 0; padding: 24px;
    }}
    h1 {{ color: #ffffff; margin-bottom: 4px; }}
    .subtitle {{ color: #8b949e; margin-bottom: 24px; font-size: 14px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }}
    .card-title {{ font-size: 12px; text-transform: uppercase; color: #8b949e; letter-spacing: 0.5px; }}
    .card-value {{ font-size: 24px; font-weight: bold; color: #ffffff; margin-top: 8px; }}
    .card-sub {{ font-size: 12px; color: var(--accent); margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--border); border-radius: 6px; font-size: 13px; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); text-align: left; }}
    th {{ background: #21262d; color: #ffffff; font-weight: 600; }}
    a {{ color: var(--blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .badge {{ background: #1f6feb33; color: var(--blue); padding: 2px 8px; border-radius: 12px; font-size: 11px; }}
  </style>
</head>
<body>
  <h1>The Polite Scraper · Dashboard</h1>
  <div class="subtitle">Last fresh: {report.start_time} · Run duration: {report.duration_seconds:.2f}s</div>

  <div class="metrics">
    <div class="card">
      <div class="card-title">Total Books</div>
      <div class="card-value">{len(records)}</div>
      <div class="card-sub">Validated 100%</div>
    </div>
    <div class="card">
      <div class="card-title">Price Range</div>
      <div class="card-value">£{min_price:.2f} - £{max_price:.2f}</div>
      <div class="card-sub">Avg: £{avg_price:.2f}</div>
    </div>
    <div class="card">
      <div class="card-title">Observability</div>
      <div class="card-value">{report.cache_hits} hits</div>
      <div class="card-sub">{report.pages_fetched} live fetches</div>
    </div>
    <div class="card">
      <div class="card-title">Failures</div>
      <div class="card-value">{report.failed_pages}</div>
      <div class="card-sub">Errors: {report.invalid_records}</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Price</th>
        <th>Rating</th>
        <th>Availability</th>
        <th>Link</th>
        <th>Description Snippet</th>
      </tr>
    </thead>
    <tbody>
      {rows_str}
    </tbody>
  </table>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    return output_path
