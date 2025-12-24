import keyring
import json
import socket
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from .config import APP_NAME

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    token_data = None

    def do_POST(self):
        if self.path == '/callback':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            OAuthCallbackHandler.token_data = json.loads(post_data)
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        return # Silence server logs

class AuthManager:
    """Manages authentication state and OS keyring interactions."""
    
    SERVICE_NAME = "locknkey-cli"
    
    def get_stored_token(self):
        token_json = keyring.get_password(self.SERVICE_NAME, "firebase_token")
        if token_json:
            return json.loads(token_json)
        return None

    def store_token(self, token_data: dict):
        keyring.set_password(self.SERVICE_NAME, "firebase_token", json.dumps(token_data))

    def logout(self):
        try:
            keyring.delete_password(self.SERVICE_NAME, "firebase_token")
        except:
            pass

    def login_flow(self):
        """Starts a local server and opens the browser for authentication."""
        # Find a free port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))
        port = sock.getsockname()[1]
        sock.close()

        server = HTTPServer(('localhost', port), OAuthCallbackHandler)
        OAuthCallbackHandler.token_data = None
        
        # Start server in thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        # Open Browser e.g. "http://localhost:3000/cli-auth?port=..."
        # TODO: Make the URL configurable
        dashboard_url = f"https://lock-box-ashy.vercel.app/cli-auth?port={port}"
        print(f"Opening browser to: {dashboard_url}")
        webbrowser.open(dashboard_url)

        print("Waiting for authentication...")
        while OAuthCallbackHandler.token_data is None:
            pass
        
        server.shutdown()
        
        token = OAuthCallbackHandler.token_data
        self.store_token(token)
        print(f"Successfully logged in as {token.get('email')}")
        return token
