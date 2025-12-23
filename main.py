import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
import os
import uuid

from datetime import datetime, timezone
from recorder import append_record
from recorder import get_monthly_log_file
from scraper import get_usd_rate, get_reference_rate

# configuration
BASE_URL = "https://www.bca.co.id/id/informasi/kurs"
VALID_MODES = {"always", "on_change", "on_threshold"}
VALID_THRESHOLDS = set(
    range(16000, 17501, 10)
)  # Example valid thresholds from 16000 to 17500 with step of 10
TOPIC_PREFIX = "finuaz-bca-usd-idr-"
REFERENCE_URL = "https://markets.ft.com/data/currencies/ajax/conversion?amount=1&baseCurrency=USD&comparison=IDR"


def detect_environment() -> str:
    if os.getenv("GITHUB_ACTIONS") == "true":
        return "github_actions"
    return "local"


# helper functions
def topic_for_target(target: int) -> str:
    return f"{TOPIC_PREFIX}{target}"


def extract_threshold_from_topic(topic: str) -> int | None:
    if not topic.startswith(TOPIC_PREFIX):
        return None
    try:
        return int(topic[len(TOPIC_PREFIX) :])
    except ValueError:
        return None


def send_notification(rate: int, target: int):
    topic = topic_for_target(target)
    message = (
        f"💰 USD reached {format_idr(rate)} IDR\n"
        f"🎯 Threshold crossed: {format_idr(target)}"
    )

    requests.post(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"))


def format_idr(value: int | float) -> str:
    # Format with dot thousand separator and comma decimal
    s = f"{value:,.2f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


# tracking triggered notifications
def load_triggered():
    try:
        with open("triggered.txt") as f:
            return set(map(int, f.read().splitlines()))
    except FileNotFoundError:
        return set()


def save_triggered(triggered):
    with open("triggered.txt", "w") as f:
        for t in triggered:
            f.write(f"{t}\n")


# main function
def main():

    run_start = time.perf_counter()
    now = datetime.now(timezone.utc).astimezone()

    triggered_now = []

    # reset per-run state
    if os.path.exists("triggered.txt"):
        os.remove("triggered.txt")

    usd_rate_data = get_usd_rate()

    buy_rate = usd_rate_data["buy"]
    if not buy_rate:
        print("Gagal ambil data kurs.")
        return

    print(f"Kurs beli USD saat ini: {format_idr(buy_rate)} IDR")

    triggered = load_triggered()

    for target in VALID_THRESHOLDS:
        if buy_rate >= target and target not in triggered:
            send_notification(buy_rate, target)
            triggered.add(target)
            triggered_now.append(target)
            time.sleep(0.15)  # brief pause to avoid spamming

    save_triggered(triggered)

    reference_value = get_reference_rate()

    elapsed_ms = int((time.perf_counter() - run_start) * 1000)

    record = {
        "run_id": str(uuid.uuid4()),
        "environment": detect_environment(),
        "timestamp": now.isoformat(),
        "http_status": usd_rate_data["http_status"],
        "source": "bca",
        "currency_pair": "USD/IDR",
        "rate_type": "eRate-buy",
        "buy-rate": usd_rate_data["buy"],
        "sell-rate": usd_rate_data["sell"],
        "delta_rate": usd_rate_data["sell"] - usd_rate_data["buy"],
        "reference-rate": reference_value,
        "reference-delta": reference_value - usd_rate_data["buy"],
        "thresholds_checked": sorted(VALID_THRESHOLDS),
        "thresholds_triggered": triggered_now,
        "notification_count": len(triggered_now),
        "mode": "on_threshold",
        "schema_version": 2.1,
        "latency_ms": elapsed_ms,
    }

    append_record(record)

    print(f"⏱ Run completed in {elapsed_ms:.2f} ms")


if __name__ == "__main__":
    main()
