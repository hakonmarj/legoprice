import argparse
import csv
import gzip
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    import requests
except Exception:
    requests = None


STORE_MODULES = {
    "coolshop": "scrapers.legoprice_coolshop",
    "kubbabudin": "scrapers.legoprice_kubbabudin",
    "boozt": "scrapers.legoprice_boozt",
    "hagkaup": "scrapers.legoprice_hagkaup",
    "kidsworld": "scrapers.legoprice_kidsworld",
    "elko": "scrapers.legoprice_elko",
}

DEFAULT_STORES = ["coolshop", "kubbabudin", "boozt", "hagkaup", "kidsworld", "elko"]
SETS_PATH = Path("data/sets.csv")


def ensure_directories():
    for path in [
        Path("data"),
        Path("data/store_products"),
        Path("data/archive"),
    ]:
        path.mkdir(parents=True, exist_ok=True)


def is_valid_sets_csv(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            return bool(header) and header[0] == "set_num"
    except Exception:
        return False


def download_file(url: str, destination: Path, timeout: int = 45):
    if requests is None:
        raise RuntimeError("requests is not installed")
    response = requests.get(url, timeout=timeout, stream=True)
    response.raise_for_status()
    with destination.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                handle.write(chunk)


def fetch_latest_sets_csv() -> bool:
    ensure_directories()
    tmp_path = Path("data/archive/sets.download.tmp")
    gz_tmp_path = Path("data/archive/sets.csv.gz")

    url_candidates = []
    downloads_page = "https://rebrickable.com/downloads/"
    if requests is not None:
        try:
            page = requests.get(downloads_page, timeout=25)
            page.raise_for_status()
            html = page.text
            discovered = re.findall(r'https://cdn\.rebrickable\.com/media/downloads/sets\.csv(?:\.gz)?', html)
            for url in discovered:
                if url not in url_candidates:
                    url_candidates.append(url)
        except Exception as error:
            print(f"⚠️ Could not parse {downloads_page}: {error}")

    url_candidates.extend([
        "https://cdn.rebrickable.com/media/downloads/sets.csv.gz",
        "https://cdn.rebrickable.com/media/downloads/sets.csv",
    ])

    for url in url_candidates:
        try:
            print(f"Fetching latest sets file from: {url}")
            if url.endswith(".gz"):
                download_file(url, gz_tmp_path)
                with gzip.open(gz_tmp_path, "rb") as source, tmp_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
            else:
                download_file(url, tmp_path)

            if is_valid_sets_csv(tmp_path):
                shutil.move(str(tmp_path), str(SETS_PATH))
                print(f"✅ Updated {SETS_PATH}")
                return True
            print("⚠️ Downloaded file did not validate as sets.csv; trying next source.")
        except Exception as error:
            print(f"⚠️ Failed to fetch from {url}: {error}")

    print("⚠️ Could not fetch latest sets.csv from Rebrickable.")
    return is_valid_sets_csv(SETS_PATH)


def run_command(command, label: str) -> bool:
    print(f"\n{'=' * 70}")
    print(f"Running: {label}")
    print(f"Command: {' '.join(command)}")
    print(f"{'=' * 70}\n")
    try:
        result = subprocess.run(command, check=True)
        if result.returncode == 0:
            print(f"✅ {label} completed successfully")
            return True
    except subprocess.CalledProcessError as error:
        print(f"❌ Failed: {label} ({error})")
    except Exception as error:
        print(f"❌ Unexpected failure in {label}: {error}")
    return False


def parse_args():
    parser = argparse.ArgumentParser(description="Run LEGO scraping and aggregation pipeline.")
    parser.add_argument(
        "--stores",
        nargs="+",
        choices=sorted(STORE_MODULES.keys()),
        default=DEFAULT_STORES,
        help="Store scrapers to run (default: all stores)",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip store scrapers and only run aggregate/enrichment steps",
    )
    parser.add_argument(
        "--skip-sets-update",
        action="store_true",
        help="Skip downloading the latest sets.csv before running",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=1.0,
        help="Delay between pipeline steps (default: 1.0)",
    )
    parser.add_argument(
        "--with-bricklink",
        action="store_true",
        help="Run BrickLink enrichment after aggregations",
    )
    parser.add_argument(
        "--bricklink-workers",
        type=int,
        default=6,
        help="Worker count for BrickLink enrichment (default: 6)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_directories()

    print("Starting LEGO price pipeline...")
    print(f"Stores selected: {', '.join(args.stores)}")

    if not args.skip_sets_update:
        if not fetch_latest_sets_csv():
            print("❌ No valid data/sets.csv available; stopping pipeline.")
            return 1
    elif not is_valid_sets_csv(SETS_PATH):
        print("❌ --skip-sets-update was used but data/sets.csv is missing/invalid.")
        return 1

    steps = []
    if not args.skip_scrape:
        for store in args.stores:
            steps.append(([sys.executable, "-m", STORE_MODULES[store]], f"scraper:{store}"))
    else:
        print("Scraping step skipped.")

    steps.extend([
        ([sys.executable, "aggregate_prices.py"], "aggregate_prices"),
        ([sys.executable, "aggregate_cheapest_prices.py"], "aggregate_cheapest_prices"),
    ])

    if args.with_bricklink:
        steps.append((
            [
                sys.executable,
                "enrich_bricklink_prices.py",
                "data/aggregated_products.json",
                "--workers",
                str(max(1, min(args.bricklink_workers, 16))),
            ],
            "enrich_bricklink_prices",
        ))

    for command, label in steps:
        if not run_command(command, label):
            print(f"\n❌ Stopping process due to failure in {label}")
            return 1
        time.sleep(max(0.0, args.delay_seconds))

    print("\n🎉 Pipeline completed successfully!")
    print("Outputs:")
    print(" - data/store_products/*.json")
    print(" - data/aggregated_products.json")
    print(" - data/aggregated_cheapest_prices.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())