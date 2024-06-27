import os
import requests
import logging
from updater import download_binance_monthly_data, download_binance_daily_data, download_coingecko_data, download_cmc_data, download_portalsfi_data
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable for inference API address
INFERENCE_ADDRESS = os.getenv("INFERENCE_API_ADDRESS")

if not INFERENCE_ADDRESS:
    logging.error("INFERENCE_API_ADDRESS environment variable not set.")
    exit(1)

update_url = f"{INFERENCE_ADDRESS}/update"

logging.info("UPDATING INFERENCE WORKER DATA")

try:
    response = requests.get(update_url)
    response.raise_for_status()

    content = response.text

    if content == "0":
        logging.info("Update signal received: Proceeding with data update")
        
        # Binance data
        logging.info("Starting download of Binance data...")
        binance_data_path = os.path.join("data", "binance/futures-klines")
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

        logging.info("Data update process completed successfully")
        exit(0)
    else:
        logging.error("Update signal not received: Response content is not '0'")
        exit(1)
except requests.RequestException as e:
    logging.error(f"Request to update endpoint failed with error: {e}")
    exit(1)
