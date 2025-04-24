from flask import Flask
from threading import Thread
import os

# Create a separate Flask app for the keep-alive server
keep_alive_app = Flask('keep-alive')

@keep_alive_app.route('/')
def home():
    return "Bot Aktif"

def run():
    # Run the keep-alive server
    keep_alive_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Start the keep-alive server in a separate thread
    t = Thread(target=run)
    t.daemon = True  # This thread will exit when the main program exits
    t.start()

# If this file is run directly, start the keep-alive server
if __name__ == "__main__":
    keep_alive()