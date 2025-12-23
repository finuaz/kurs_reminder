import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.bca.co.id/id/informasi/kurs"
REFERENCE_URL = "https://markets.ft.com/data/currencies/ajax/conversion?amount=1&baseCurrency=USD&comparison=IDR"


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
