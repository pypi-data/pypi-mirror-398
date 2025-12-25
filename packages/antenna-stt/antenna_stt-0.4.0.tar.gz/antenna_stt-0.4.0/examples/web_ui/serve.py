#!/usr/bin/env python3
"""Simple HTTP server for the Antenna STT web UI.

Usage:
    python serve.py [port]

Default port is 3000. Open http://localhost:3000 in your browser.
"""

import http.server
import socketserver
import sys
import os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000

# Change to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = http.server.SimpleHTTPRequestHandler

# Enable CORS for development
class CORSHandler(Handler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

with socketserver.TCPServer(("", PORT), CORSHandler) as httpd:
    print(f"Antenna STT Web UI")
    print(f"==================")
    print(f"")
    print(f"Serving at: http://localhost:{PORT}")
    print(f"")
    print(f"Make sure the Antenna server is running:")
    print(f"  cargo run --bin antenna-server --features server -- --model tiny")
    print(f"")
    print(f"Press Ctrl+C to stop.")
    print(f"")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
