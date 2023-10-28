# This is Traffic Steering xApp version 1.0.0 by Milad Natanzi
#ts-xapp.py
import json
import os
import sys
import logging
from flask import Flask, jsonify
import subprocess
import signal
from ricxappframe.xapp_frame import RMRXapp
from subscription_manager import SubscriptionManager
import default_handler
from rmr_health_check import rmr_health_check
from sdl_health_check import sdl_health_check
from traffic_steering import traffic_steering
# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s:%(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler('ts-xapp.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create an RMR xApp instance
rmr_xapp = RMRXapp(default_handler.default_rmr_handler, rmr_port=4560)

# Provide the correct URI for the Subscription Manager
subscription_manager_uri = "http://10.244.0.18:3800/"

# Create an instance of the SubscriptionManager
subscription_manager = SubscriptionManager(uri=subscription_manager_uri, local_address="0.0.0.0", local_port=8088)

# Set the SubscriptionManager in default_handler
default_handler.set_subscription_manager(subscription_manager)

app = Flask(__name__)

@app.route('/rmr_health_check', methods=['POST'])
def run_rmr_health_check():
    try:
        message = rmr_health_check(rmr_xapp)
        logging.info(message)
        return jsonify(message=message)
    except Exception as e:
        logging.error(f"Error executing RMR Health Check: {str(e)}")
        return jsonify(message=f"Error: {str(e)}"), 500

@app.route('/sdl_health_check', methods=['POST'])
def run_sdl_health_check():
    try:
        message = sdl_health_check()
        logging.info(message)
        return jsonify(message=message)
    except Exception as e:
        logging.error(f"Error executing SDL Health Check: {str(e)}")
        return jsonify(message=f"Error: {str(e)}"), 500

@app.route('/traffic_steering', methods=['POST'])
def run_traffic_steering():
    try:
        message = traffic_steering()
        logging.info(message)
        return jsonify(message=message)
    except Exception as e:
        logging.error(f"Error executing Traffic Steering: {str(e)}")
        return jsonify(message=f"Error: {str(e)}"), 500

# Store the subprocess reference
try:
    logging.debug("Attempting to start the dashboard subprocess...")
    dashboard_process = subprocess.Popen(
        ["python3", "/app/ts-xapp/src/dashboard.py"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    logging.debug("Dashboard subprocess started successfully.")
except Exception as e:
    logging.error(f"Failed to start the dashboard subprocess: {str(e)}")

# Define the signal handler function
def terminate_process(signum, frame):
    dashboard_process.terminate()
    logging.info("Dashboard subprocess terminated.")
    exit(0)

# Attach the handler to SIGINT (Ctrl+C) and SIGTERM (termination signal)
signal.signal(signal.SIGINT, terminate_process)
signal.signal(signal.SIGTERM, terminate_process)

if __name__ == "__main__":
    logging.info("ts-xApp starting...")

    # Initialize subscriptions
    subscription_manager.initialize_subscriptions()

    app.run(host='0.0.0.0', port=5000)  # go to http://127.0.0.1:5000 and select the menu
