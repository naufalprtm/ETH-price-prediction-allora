import os
import requests
import sys
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable for inference API address
INFERENCE_ADDRESS = os.getenv("INFERENCE_API_ADDRESS")

if not INFERENCE_ADDRESS:
    logging.error("INFERENCE_API_ADDRESS environment variable not set.")
    sys.exit(1)

def process(token_name, data_source):
    """
    Sends a GET request to the inference API with the specified token name and data source.

    Args:
        token_name (str): The token name to query the inference API.
        data_source (str): The data source to use for inference ('binance', 'coingecko', 'cmc', 'portalsfi').

    Returns:
        str: The response content from the API.
    """
    try:
        logging.info(f"Sending request to inference API for token: {token_name} using data source: {data_source}")
        response = requests.get(f"{INFERENCE_ADDRESS}/inference/{token_name}?source={data_source}")
        response.raise_for_status()
        logging.info(f"Received response from inference API: {response.status_code}")
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error making request to inference API: {e}")
        raise

if __name__ == "__main__":
    # Check and parse command line arguments
    if len(sys.argv) < 6:
        value = json.dumps({
            "error": f"Not enough arguments provided: {len(sys.argv) - 1}, expected 5 arguments: topic_id, blockHeight, blockHeightEval, default_arg, data_source"
        })
        logging.error(f"Not enough arguments provided: {len(sys.argv) - 1}, expected 5 arguments.")
    else:
        try:
            topic_id = sys.argv[1]
            blockHeight = sys.argv[2]
            blockHeightEval = sys.argv[3]
            default_arg = sys.argv[4]
            data_source = sys.argv[5]

            logging.info(f"Received arguments: topic_id={topic_id}, blockHeight={blockHeight}, blockHeightEval={blockHeightEval}, default_arg={default_arg}, data_source={data_source}")

            response_inference = process(token_name=default_arg, data_source=data_source)
            response_dict = {"infererValue": response_inference}
            value = json.dumps(response_dict)
            logging.info(f"Processed inference successfully. Response: {response_dict}")
        except Exception as e:
            logging.error(f"Error processing inference: {e}")
            value = json.dumps({"error": str(e)})

    print(value)
    logging.info("Script execution completed.")
