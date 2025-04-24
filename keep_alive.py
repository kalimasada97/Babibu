import os
import logging
import threading
import time
import http.server
import socketserver

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeepAliveHandler(http.server.SimpleHTTPRequestHandler):
    """Simple HTTP request handler that returns a status message."""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot Aktif - Crypto Trading Signal Tracker Running")
        
    def log_message(self, format, *args):
        """Override to reduce log verbosity"""
        return

def run_server():
    """Run the HTTP server in a separate thread."""
    ports = [8080, 8081, 8082, 8083]  # Try multiple ports in case one is in use
    handler = KeepAliveHandler
    
    for port in ports:
        try:
            # Allow socket reuse to prevent "Address already in use" errors
            socketserver.TCPServer.allow_reuse_address = True
            with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
                logger.info(f"Keep-alive server started on port {port}")
                httpd.serve_forever()
                return  # If successful, exit the function
        except OSError as e:
            logger.error(f"Error starting keep-alive server on port {port}: {e}")
            # Try the next port
            continue
    
    # If all ports failed, wait and try again
    logger.error("All ports failed, retrying after delay")
    time.sleep(30)
    run_server()  # Recursive retry

def keep_alive():
    """Start the keep-alive server thread."""
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info("Keep-alive thread started")
    return server_thread

# If this script is run directly, start the keep-alive server
if __name__ == "__main__":
    try:
        keep_alive()
        # Keep the main thread running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Keep-alive server stopped")
        exit(0)