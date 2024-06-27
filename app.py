import os
import json
import pickle
import pandas as pd
import numpy as np
import threading
import logging
from datetime import datetime
from flask import Flask, jsonify, Response, request
from model import download_binance_data, format_binance_data, download_coingecko_data, download_cmc_data, download_portalsfi_data, train_model
from config import model_file_path, data_base_path
import requests
import torch
from transformers import pipeline

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def update_data():
    """Download price data, format data, and train model."""
    logging.info("Starting data update process.")
    try:
        # Update Binance data
        logging.info("Updating Binance data...")
        download_binance_data()
        format_binance_data()
        binance_data_path = os.path.join(data_base_path, "eth_price_data.csv")
        if os.path.exists(binance_data_path):
            df = pd.read_csv(binance_data_path)
            logging.info(f"Binance data: {df.head()}")
            train_model(binance_data_path, model_file_path)
            logging.info(f"Binance data file found and model trained at {datetime.now()}")
        else:
            logging.error("Binance data file not found after download.")

        # Update CoinGecko data
        logging.info("Updating CoinGecko data...")
        download_coingecko_data()
        coingecko_data_path = os.path.join(data_base_path, "coingecko_eth_price_data.csv")
        if os.path.exists(coingecko_data_path):
            df = pd.read_csv(coingecko_data_path)
            logging.info(f"CoinGecko data: {df.head()}")
            train_model(coingecko_data_path, os.path.join(data_base_path, "eth_model.pkl"))
            logging.info(f"CoinGecko data file found and model trained at {datetime.now()}")
        else:
            logging.error("CoinGecko data file not found after download.")

        # Update CoinMarketCap data
        logging.info("Updating CoinMarketCap data...")
        download_cmc_data()
        cmc_data_path = os.path.join(data_base_path, "cmc_eth_price_data.csv")
        if os.path.exists(cmc_data_path):
            df = pd.read_csv(cmc_data_path)
            logging.info(f"CoinMarketCap data: {df.head()}")
            train_model(cmc_data_path, os.path.join(data_base_path, "cmc_model.pkl"))
            logging.info(f"CoinMarketCap data file found and model trained at {datetime.now()}")
        else:
            logging.error("CoinMarketCap data file not found after download.")

        # Update Portals.fi data
        logging.info("Updating Portals.fi data...")
        download_portalsfi_data()
        portalsfi_data_path = os.path.join(data_base_path, "portalsfi_eth_price_data.csv")
        if os.path.exists(portalsfi_data_path):
            df = pd.read_csv(portalsfi_data_path)
            logging.info(f"Portals.fi data: {df.head()}")
            train_model(portalsfi_data_path, os.path.join(data_base_path, "portalsfi_model.pkl"))
            logging.info(f"Portals.fi data file found and model trained at {datetime.now()}")
        else:
            logging.error("Portals.fi data file not found after download.")

        logging.info("Data update process completed successfully.")
    except Exception as e:
        logging.error(f"Data update process failed: {e}")

def get_eth_inference(data_source='binance'):
    """Load ETH model and predict current price."""
    model_path_map = {
        'binance': model_file_path,
        'coingecko': os.path.join(data_base_path, "eth_model.pkl"),
        'cmc': os.path.join(data_base_path, "cmc_model.pkl"),
        'portalsfi': os.path.join(data_base_path, "portalsfi_model.pkl")
    }

    data_path_map = {
        'binance': os.path.join(data_base_path, "eth_price_data.csv"),
        'coingecko': os.path.join(data_base_path, "coingecko_eth_price_data.csv"),
        'cmc': os.path.join(data_base_path, "cmc_eth_price_data.csv"),
        'portalsfi': os.path.join(data_base_path, "portalsfi_eth_price_data.csv")
    }

    if data_source not in model_path_map:
        raise ValueError(f"Data source '{data_source}' not supported")

    try:
        with open(model_path_map[data_source], "rb") as f:
            loaded_model = pickle.load(f)
            logging.info(f"Loaded model for {data_source} successfully at {datetime.now()}")
    except FileNotFoundError:
        logging.error(f"Model file for {data_source} not found.")
        raise

    now_timestamp = pd.Timestamp(datetime.now()).timestamp()
    X_new = np.array([now_timestamp]).reshape(-1, 1)
    
    try:
        current_price_pred = loaded_model.predict(X_new)
        logging.info(f"Generated inference: {current_price_pred[0][0]} for source {data_source} at {datetime.now()}")
        return current_price_pred[0][0]
    except Exception as e:
        logging.error(f"Prediction error for {data_source}: {e}")
        raise

@app.route("/inference/<string:token>")
def generate_inference(token):
    """Generate inference for given token."""
    logging.info(f"Received inference request for token: {token} at {datetime.now()}")
    data_source = request.args.get('source', default='binance', type=str)
    
    if token.upper() == "ETH":
        try:
            # Read the latest data to log details
            data_path_map = {
                'binance': os.path.join(data_base_path, "eth_price_data.csv"),
                'coingecko': os.path.join(data_base_path, "coingecko_eth_price_data.csv"),
                'cmc': os.path.join(data_base_path, "cmc_eth_price_data.csv"),
                'portalsfi': os.path.join(data_base_path, "portalsfi_eth_price_data.csv")
            }
            
            if data_source in data_path_map:
                df = pd.read_csv(data_path_map[data_source])
                latest_data = df.tail(1)
                logging.info(f"Latest data from {data_source}: {latest_data.to_dict(orient='records')}")

            inference = get_eth_inference(data_source)
            logging.info(f"Inference for ETH from {data_source} successfully generated at {datetime.now()}")
            return Response(str(inference), status=200)
        except Exception as e:
            logging.error(f"Inference generation failed: {e}")
            return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')
    else:
        error_msg = "Token is required" if not token else "Token not supported"
        logging.error(f"Inference request failed: {error_msg} at {datetime.now()}")
        return Response(json.dumps({"error": error_msg}), status=400, mimetype='application/json')

@app.route("/update", methods=["GET"])
def update():
    """Update data and return status."""
    try:
        thread = threading.Thread(target=update_data)
        thread.start()
        logging.info(f"Update process started at {datetime.now()}")
        return Response(json.dumps({"status": "update started"}), status=200, mimetype='application/json')
    except Exception as e:
        logging.error(f"Failed to start update process: {e}")
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

@app.route("/status")
def status():
    """Return status of the model and data."""
    try:
        with open(model_file_path, "rb") as f:
            loaded_model = pickle.load(f)
            logging.info(f"Model loaded successfully at {datetime.now()}")
        return jsonify({"status": "Model loaded successfully"})
    except Exception as e:
        logging.error(f"Status check failed: {e}")
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

if __name__ == "__main__":
    update_data()
    app.run(host="0.0.0.0", port=8022)
