import requests
from bs4 import BeautifulSoup
import locale

from dotenv import load_dotenv
import os

URL = "https://www.bca.co.id/id/informasi/kurs"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}

locale.setlocale(locale.LC_NUMERIC, "id_ID.UTF-8")

target = 15000
parsed_target = locale.format_string("%.2f", target, grouping=True).replace(".", "X").replace(",", ".").replace("X", ",")


# Send GET request
response = requests.get(URL, headers=headers)

# Check if request was successful
if response.status_code == 200:
    print("✅ Request successful!\n")
else:
    print(f"❌ Failed to retrieve data, status code: {response.status_code}")
    exit()

# Parse HTML menggunakan BeautifulSoup
soup = BeautifulSoup(response.text, "lxml")

# Print sebagian teks halaman untuk memastikan kita mendapat konten
# print("========= Part of received HTML =========")
# print(soup.text[:5000])  # tampilkan 500 karakter pertama

# (opsional) tampilkan title halaman
title = soup.find("title").text if soup.find("title") else "Not found"
print("\nPage Title:", title)

tables = soup.find_all("table")
if tables:
    print(f"\nFound {len(tables)} tables on the page.")

usd_columns = soup.find_all("tr", class_="m-table-body-row", code="USD")
if usd_columns:
    print(usd_columns[0].text)

    usd_data = {}
    for td in usd_columns[0].find_all("td", class_="rate-column", attrs={"rate-type": "eRate-buy"}):
        usd_data["eRate-buy"] = td.text.strip()

    for td in usd_columns[0].find_all("td", class_="rate-column", attrs={"rate-type": "eRate-sell"}):
        usd_data["eRate-sell"] = td.text.strip()

    print("\nUSD Data:", usd_data)

    buy_rate = int(usd_data["eRate-buy"].replace(",00", "").replace(".", ""))
    sell_rate = int(usd_data["eRate-sell"].replace(",00", "").replace(".", ""))
    print(f"\nUSD eRate Buy: {buy_rate}")
    print(f"USD eRate Sell: {sell_rate}")
    if buy_rate > target:
        print(f"Alert: USD eRate Buy is above IDR {parsed_target}!")

else:
    print("USD row not found in the table.")
    