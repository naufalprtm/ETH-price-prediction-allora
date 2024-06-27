# ETH-price-prediction-allora

This repository provides an example Allora network worker node designed to offer price predictions for Ethereum (ETH). It demonstrates the utilization of a basic inference model operating within a dedicated container and showcases its seamless integration with the Allora network infrastructure, enabling it to contribute with valuable inferences.

## Repository Origin

This code is based on the repository from the Allora Network:
[https://github.com/allora-network/basic-coin-prediction-node/tree/main](https://github.com/allora-network/basic-coin-prediction-node/tree/main)

## Components

### Inference (app.py)
This Flask app exposes endpoints to generate inferences and update the model. It acts as the gateway to the model from external requests.

#### Endpoints:
- `/inference/<string:token>`: Generates inference for the given token.
- `/update`: Updates the model by downloading and training with the latest data.
- `/status`: Checks the status of the model and data.

### Updater (update_app.py)
This service is designed to hit the `/update` endpoint on the inference service, ensuring the model state is updated when needed. It can also be scheduled to run periodically.

### Worker (main.py)
This script combines the Allora inference base, node function, and custom logic. The Allora chain makes requests to the head node, which then directs requests to the workers.

### Configuration
The scripts utilize environment variables for configuration:
- `INFERENCE_API_ADDRESS`: The address of the inference API.

## Usage

### Running the Inference Service
To start the Flask app for generating inferences and updating the model:
```bash
python app.py
