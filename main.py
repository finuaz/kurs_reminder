import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
import os
import uuid

# load_dotenv()

from datetime import datetime, timezone
from recorder import append_record
from recorder import get_monthly_log_file

# configuration

BASE_URL = "https://www.bca.co.id/id/informasi/kurs"
VALID_MODES = {"always", "on_change", "on_threshold"}
VALID_THRESHOLDS = set(
    range(15000, 17501, 100)
)  # Example valid thresholds from 15000 to 17500 with step of 100
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


# scraping function
def get_usd_rate():
    buy_rate = None
    sell_rate = None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }

    response = requests.get(BASE_URL, headers=headers)
    print("=== DEBUG RESPONSE ===")
    print("Status:", response.status_code)
    if response.status_code == 200:
        print("✅ Request successful!")

        # Parsing result using BeautifulSoup
        soup = BeautifulSoup(response.text, "lxml")

        # Show page title
        title = soup.find("title").text if soup.find("title") else "Not found"
        print("Page Title:", title)

        # work with table
        tables = soup.find_all("table")
        if tables:
            print(f"\nFound {len(tables)} tables on the page.")
        else:
            print("No tables found on the page.")
            exit()

        usd_columns = soup.find_all("tr", class_="m-table-body-row", code="USD")
        if usd_columns:
            usd_data = {}

            for td in usd_columns[0].find_all(
                "td", class_="rate-column", attrs={"rate-type": "eRate-buy"}
            ):
                usd_data["eRate-buy"] = td.text.strip()

            for td in usd_columns[0].find_all(
                "td", class_="rate-column", attrs={"rate-type": "eRate-sell"}
            ):
                usd_data["eRate-sell"] = td.text.strip()

            print("\nUSD Data:", usd_data, "\n")

            buy_rate = int(usd_data["eRate-buy"].replace(",00", "").replace(".", ""))
            sell_rate = int(usd_data["eRate-sell"].replace(",00", "").replace(".", ""))

        else:
            print("USD row not found in the table.")
    else:
        print(f"❌ Failed to retrieve data, status code: {response.status_code}")
        exit()

    return {"buy": buy_rate, "sell": sell_rate, "http_status": response.status_code}


def get_reference_rate():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }

    response = requests.get(REFERENCE_URL, headers=headers)
    if response.status_code == 200:
        print("✅ Reference request successful!")
        data = response.json()
        rate_str = data["data"]["exchangeRate"]
        parsed_rate = int(float(rate_str.replace(",", "")))
        return parsed_rate
    else:
        print(f"❌ Failed to retrieve data, status code: {response.status_code}")
        return None


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
