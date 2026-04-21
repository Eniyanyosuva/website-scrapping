import json
import subprocess
import sys
import tempfile
from pathlib import Path


def crawl_shopify_products(store_url: str, query: str, timeout_sec: int = 60) -> list[dict]:
    spider_path = Path(__file__).resolve().parents[1] / "scraper" / "shopify_spider.py"

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as out_file:
        output_path = Path(out_file.name)

    cmd = [
        sys.executable,
        "-m",
        "scrapy",
        "runspider",
        str(spider_path),
        "-a",
        f"store_url={store_url}",
        "-a",
        f"query={query}",
        "-O",
        str(output_path),
        "-s",
        "LOG_ENABLED=False",
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout_sec)
        if not output_path.exists():
            return []
        content = output_path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return []
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return []
    finally:
        if output_path.exists():
            output_path.unlink(missing_ok=True)
