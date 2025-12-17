import requests
from bs4 import BeautifulSoup
import locale
import time
from dotenv import load_dotenv
import os
from urllib.parse import urlparse, parse_qs
load_dotenv()

# configuration

CURRENCY = "USD"        # USD, EUR, SGD, JPY, etc
RATE_TYPE = "eRate"     # eRate | TT | Bank Notes

BASE_URL = "https://www.bca.co.id/id/informasi/kurs"
NTFY_TOPIC = "finuaz-bca-usd-idr-erate"
ITERATION = 600
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}?target=17000"

def get_target_rate_from_ntfy_url(url: str, default: int = 17000) -> int:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    try:
        return int(params.get("target", [default])[0])
    except (ValueError, TypeError):
        return default  

TARGET_RATE = [14000, 14500, 15000, 15500, 16000, 16500, 17000, 17500] # target rate in IDR to trigger notification
# print(f"Target rate set to IDR {TARGET_RATE}")


# def format_idr(number):
#     locale.setlocale(locale.LC_NUMERIC, "id_ID.UTF-8")
#     return locale.format_string("%.2f", number, grouping=True).replace(".", "X").replace(",", ".").replace("X", ",")

def format_idr(value: int | float) -> str:
    # Format with dot thousand separator and comma decimal
    s = f"{value:,.2f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def topic_for_target(target: int) -> str:
    return f"finuaz-bca-usd-idr-erate-{target}"


def get_usd_rate():
    buy_rate = None
    sell_rate = None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }
 
    # Send request and validate response
    response = requests.get(BASE_URL, headers=headers)
    print("=== DEBUG RESPONSE ===")
    print("Status:", response.status_code)
    print("Headers:", response.headers)
    print("First 500 chars of HTML:")
    print(response.text[:500])
    print("======================")

    # Check if request was successful
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
            for td in usd_columns[0].find_all("td", class_="rate-column", attrs={"rate-type": "eRate-buy"}):
                usd_data["eRate-buy"] = td.text.strip()

            for td in usd_columns[0].find_all("td", class_="rate-column", attrs={"rate-type": "eRate-sell"}):
                usd_data["eRate-sell"] = td.text.strip()

            print("\nUSD Data:", usd_data, "\n")

            buy_rate = int(usd_data["eRate-buy"].replace(",00", "").replace(".", ""))
            sell_rate = int(usd_data["eRate-sell"].replace(",00", "").replace(".", ""))

            # if buy_rate > TARGET_RATE:
            #     print(f"ALERT !!!\nUSD eRate Buy is above IDR {format_idr(TARGET_RATE)}!!!\nCurrent rate: IDR {usd_data['eRate-buy']}!!!")

        else:
            print("USD row not found in the table.")
    else:
        print(f"❌ Failed to retrieve data, status code: {response.status_code}")
        exit()

    return buy_rate

    # Parse HTML menggunakan BeautifulSoup
    
def send_notification(rate: int, target: int):
    topic = topic_for_target(target)
    message = (
        f"💰 USD reached {format_idr(rate)} IDR\n"
        f"🎯 Threshold crossed: {format_idr(target)}"
    )

    requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8")
    )




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

# Invoke the function
# get_usd_rate()
# def check_thresholds(rate: int, targets: list[int]):
#     for target in targets:
#         if rate >= target:
#             send_notification(rate, target)

def main():
    usd_rate = get_usd_rate()
    if not usd_rate:
        print("Gagal ambil data kurs.")
        return

    print(f"Kurs beli USD saat ini: {format_idr(usd_rate)} IDR")

    # check_thresholds(usd_rate, TARGET_RATE)

    triggered = load_triggered()

    for target in TARGET_RATE:
        if usd_rate >= target and target not in triggered:
            send_notification(usd_rate, target)
            triggered.add(target)

    save_triggered(triggered)



    # if usd_rate >= TARGET_RATE:
    #     print("🚨 Kurs sudah melebihi target, kirim notifikasi!", "\n timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
    #     send_notification(usd_rate)
    # else:
    #     print("📉 Belum mencapai target.", "\n timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    # Jalankan sekali
    main()

    # Atau jalankan periodik (contoh: tiap 30 menit)
    # while True:
    #     main()
    #     time.sleep(ITERATION) 


