import os
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base paths for data storage
data_base_path = "data"
binance_data_path = os.path.join(data_base_path, "binance/futures-klines")
coingecko_data_path = os.path.join(data_base_path, "coingecko_eth_price_data.csv")
cmc_data_path = os.path.join(data_base_path, "cmc_eth_price_data.csv")
portalsfi_data_path = os.path.join(data_base_path, "portalsfi_eth_price_data.csv")

def download_url(url, download_path):
    target_file_path = os.path.join(download_path, os.path.basename(url)) 
    if os.path.exists(target_file_path):
        logging.info(f"File already exists: {url}")
        return
    
    response = requests.get(url)
    if response.status_code == 404:
        logging.warning(f"File does not exist: {url}")
    else:
        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
        with open(target_file_path, "wb") as f:
            f.write(response.content)
        logging.info(f"Downloaded: {url} to {target_file_path}")

def download_binance_monthly_data(cm_or_um, symbols, intervals, years, months, download_path):
    if cm_or_um not in ["cm", "um"]:
        logging.error("CM_OR_UM can be only cm or um")
        return
    base_url = f"https://data.binance.vision/data/futures/{cm_or_um}/monthly/klines"
    with ThreadPoolExecutor() as executor:
        for symbol in symbols:
            for interval in intervals:
                for year in years:
                    for month in months:
                        url = f"{base_url}/{symbol}/{interval}/{symbol}-{interval}-{year}-{month}.zip"
                        executor.submit(download_url, url, download_path)

def download_binance_daily_data(cm_or_um, symbols, intervals, year, month, download_path):
    if cm_or_um not in ["cm", "um"]:
        logging.error("CM_OR_UM can be only cm or um")
        return
    base_url = f"https://data.binance.vision/data/futures/{cm_or_um}/daily/klines"
    with ThreadPoolExecutor() as executor:
        for symbol in symbols:
            for interval in intervals:
                for day in range(1, 32):
                    url = f"{base_url}/{symbol}/{interval}/{symbol}-{interval}-{year}-{month:02d}-{day:02d}.zip"
                    executor.submit(download_url, url, download_path)

def download_coingecko_data():
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=30&interval=daily"
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-HERE"  # replace with your API key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["prices"])
        df.columns = ["date", "price"]
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        df = df[:-1]
        df.to_csv(coingecko_data_path, index=False)
        logging.info(f"Downloaded CoinGecko data to {coingecko_data_path}.")
    else:
        logging.error(f"Failed to retrieve data from CoinGecko: {response.text}")

def download_cmc_data():
    url = 'https://sandbox-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
        'start': '1',
        'limit': '5000',
        'convert': 'USD'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'HERE',  # replace with your API key
    }
    response = requests.get(url, headers=headers, params=parameters)
    if response.status_code == 200:
        data = response.json()
        eth_data = next(item for item in data['data'] if item['symbol'] == 'ETH')
        df = pd.DataFrame([{
            "date": datetime.now(),
            "price": eth_data['quote']['USD']['price']
        }])
        df.to_csv(cmc_data_path, index=False)
        logging.info(f"Downloaded CoinMarketCap data to {cmc_data_path}.")
    else:
        logging.error(f"Failed to retrieve data from CoinMarketCap: {response.text}")

def download_portalsfi_data():
    url = "https://api.portals.fi/v2/tokens?search=eth&platforms=native&networks=ethereum"
    headers = {
        "Authorization": "HERE"  # replace with your API key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        eth_data = next(item for item in data if item['symbol'].upper() == 'ETH')
        df = pd.DataFrame([{
            "date": datetime.now(),
            "price": eth_data['price_usd']
        }])
        df.to_csv(portalsfi_data_path, index=False)
        logging.info(f"Downloaded Portals.fi data to {portalsfi_data_path}.")
    else:
        logging.error(f"Failed to retrieve data from Portals.fi: {response.text}")

if __name__ == "__main__":
    # Binance data
    logging.info("Starting download of Binance data...")
    download_binance_monthly_data("um", ["ETHUSDT"], ["1d"], ["2018", "2019", "2020", "2021", "2022", "2023", "2024"], ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], binance_data_path)
    current_year = datetime.now().year
    current_month = datetime.now().month
    download_binance_daily_data("um", ["ETHUSDT"], ["1d"], current_year, current_month, binance_data_path)

    # CoinGecko data
    logging.info("Starting download of CoinGecko data...")
    download_coingecko_data()

    # CoinMarketCap data
    logging.info("Starting download of CoinMarketCap data...")
    download_cmc_data()

    # Portals.fi data
    logging.info("Starting download of Portals.fi data...")
    download_portalsfi_data()
