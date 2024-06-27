import os
import pickle
from zipfile import ZipFile
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from updater import download_binance_monthly_data, download_binance_daily_data
from config import data_base_path, model_file_path
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths for data and model storage
binance_data_path = os.path.join(data_base_path, "binance/futures-klines")
training_price_data_path = os.path.join(data_base_path, "eth_price_data.csv")
coingecko_data_path = os.path.join(data_base_path, "coingecko_eth_price_data.csv")
cmc_data_path = os.path.join(data_base_path, "cmc_eth_price_data.csv")
portalsfi_data_path = os.path.join(data_base_path, "portalsfi_eth_price_data.csv")

def download_binance_data():
    """
    Download monthly and daily Binance data for ETHUSDT.
    """
    cm_or_um = "um"
    symbols = ["ETHUSDT"]
    intervals = ["1d"]
    years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]
    months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    download_path = binance_data_path

    # Download monthly data
    download_binance_monthly_data(
        cm_or_um, symbols, intervals, years, months, download_path
    )
    logging.info(f"Downloaded monthly data to {download_path}.")

    # Download daily data for the current month
    current_datetime = datetime.now()
    current_year = current_datetime.year
    current_month = current_datetime.month
    download_binance_daily_data(
        cm_or_um, symbols, intervals, current_year, current_month, download_path
    )
    logging.info(f"Downloaded daily data to {download_path}.")

def format_binance_data():
    """
    Format downloaded Binance data into a single CSV file suitable for training.
    """
    files = sorted([x for x in os.listdir(binance_data_path) if x.endswith(".zip")])

    # Exit if no files to process
    if not files:
        logging.warning("No data files found to process.")
        return

    price_df = pd.DataFrame()

    for file in files:
        zip_file_path = os.path.join(binance_data_path, file)
        with ZipFile(zip_file_path) as myzip:
            with myzip.open(myzip.filelist[0]) as f:
                line = f.readline()
                header = 0 if line.decode("utf-8").startswith("open_time") else None
            df = pd.read_csv(myzip.open(myzip.filelist[0]), header=header).iloc[:, :11]
            df.columns = [
                "start_time", "open", "high", "low", "close", "volume", "end_time",
                "volume_usd", "n_trades", "taker_volume", "taker_volume_usd"
            ]
            df.index = pd.to_datetime(df["end_time"], unit='ms')
            df.index.name = "date"
            price_df = pd.concat([price_df, df])

    # Save formatted data to CSV
    price_df.sort_index().to_csv(training_price_data_path)
    logging.info(f"Formatted data saved to {training_price_data_path}.")

def download_coingecko_data():
    """
    Download daily data from CoinGecko for ETH.
    """
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=30&interval=daily"
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": "CG-HERE"  # replace with your API key
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["prices"], columns=["date", "price"])
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        df = df[:1]  # removing today's price
        df.to_csv(coingecko_data_path, index=False)
        logging.info(f"Downloaded CoinGecko data to {coingecko_data_path}.")
    else:
        logging.error(f"Failed to retrieve data from CoinGecko: {response.text}")
        raise Exception(f"Failed to retrieve data from CoinGecko: {response.text}")

def download_cmc_data():
    """
    Download daily data from CoinMarketCap for ETH.
    """
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
        raise Exception(f"Failed to retrieve data from CoinMarketCap: {response.text}")

def download_portalsfi_data():
    """
    Download daily data from Portals.fi for ETH.
    """
    url = "https://api.portals.fi/v2/tokens?search=eth&platforms=native&networks=ethereum"
    headers = {
        "Authorization": "HERE" # replace with your API key
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
        raise Exception(f"Failed to retrieve data from Portals.fi: {response.text}")
    
def format_coingecko_data():
    """
    Format downloaded CoinGecko data into a single CSV file suitable for training.
    """
    if not os.path.exists(coingecko_data_path):
        logging.warning("No CoinGecko data found to process.")
        return

    df = pd.read_csv(coingecko_data_path)
    df.columns = ["date", "price"]
    df["date"] = pd.to_datetime(df["date"])
    df.to_csv(coingecko_data_path, index=False)
    logging.info(f"Formatted CoinGecko data saved to {coingecko_data_path}.")

def format_cmc_data():
    """
    Format downloaded CoinMarketCap data into a single CSV file suitable for training.
    """
    if not os.path.exists(cmc_data_path):
        logging.warning("No CoinMarketCap data found to process.")
        return

    df = pd.read_csv(cmc_data_path)
    df.columns = ["date", "price"]
    df["date"] = pd.to_datetime(df["date"])
    df.to_csv(cmc_data_path, index=False)
    logging.info(f"Formatted CoinMarketCap data saved to {cmc_data_path}.")

def format_portalsfi_data():
    """
    Format downloaded Portals.fi data into a single CSV file suitable for training.
    """
    if not os.path.exists(portalsfi_data_path):
        logging.warning("No Portals.fi data found to process.")
        return

    df = pd.read_csv(portalsfi_data_path)
    df.columns = ["date", "price"]
    df["date"] = pd.to_datetime(df["date"])
    df.to_csv(portalsfi_data_path, index=False)
    logging.info(f"Formatted Portals.fi data saved to {portalsfi_data_path}.")

def train_model(data_path, model_save_path):
    """
    Train a linear regression model on the formatted price data.
    """
    # Load the price data
    price_data = pd.read_csv(data_path, parse_dates=["date"])

    # Prepare the data for training
    df = pd.DataFrame()
    df["date"] = price_data["date"].map(pd.Timestamp.timestamp)
    df["price"] = price_data["price"]

    # Reshape the data for sklearn
    x = df["date"].values.reshape(-1, 1)
    y = df["price"].values.reshape(-1, 1)

    # Split data into training and test sets
    x_train, _, y_train, _ = train_test_split(x, y, test_size=0.2, random_state=0)

    # Train the linear regression model
    model = LinearRegression()
    model.fit(x_train, y_train)

    # Ensure the model directory exists
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)

    # Save the trained model to a file
    with open(model_save_path, "wb") as f:
        pickle.dump(model, f)

    logging.info(f"Trained model saved to {model_save_path}")

if __name__ == "__main__":
    # Binance data
    download_binance_data()
    format_binance_data()
    train_model(training_price_data_path, model_file_path)
    
    # CoinGecko data
    download_coingecko_data()
    format_coingecko_data()
    train_model(coingecko_data_path, os.path.join(data_base_path, "coingecko_eth_model.pkl"))

    # CoinMarketCap data
    download_cmc_data()
    format_cmc_data()
    train_model(cmc_data_path, os.path.join(data_base_path, "cmc_eth_model.pkl"))

    # Portals.fi data
    download_portalsfi_data()
    format_portalsfi_data()
    train_model(portalsfi_data_path, os.path.join(data_base_path, "portalsfi_eth_model.pkl"))
