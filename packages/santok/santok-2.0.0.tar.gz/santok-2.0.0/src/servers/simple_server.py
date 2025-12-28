#!/usr/bin/env python3
"""
Simple HTTP Server for SanTOK (No FastAPI dependencies)
Uses only standard library for maximum compatibility
"""

import http.server
import socketserver
import json
import urllib.parse
import sys
import os
import time
from typing import Dict, List, Any

# Add src directory to path to import backend files
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Import backend files
try:
    from core.core_tokenizer import tokenize_text, reconstruct_from_tokens
    import core.core_tokenizer as KT
    print("[OK] Successfully imported core modules")
except ImportError as e:
    print(f"[ERROR] Error importing core modules: {e}")
    sys.exit(1)

class SanTOKHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for SanTOK API"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_health_response()
        elif self.path == '/':
            self.send_welcome_response()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/tokenize':
            self.handle_tokenize()
        elif self.path == '/decode':
            self.handle_decode()
        else:
            self.send_error(404, "Not Found")
    
    def send_health_response(self):
        """Send health check response"""
        response = {
            "status": "healthy",
            "service": "SanTOK Tokenizer",
            "version": "1.0.0",
            "timestamp": time.time()
        }
        self.send_json_response(response)
    
    def send_welcome_response(self):
        """Send welcome message"""
        response = {
            "message": "Welcome to SanTOK Tokenizer API",
            "version": "1.0.0",
            "endpoints": {
                "POST /tokenize": "Tokenize text",
                "POST /decode": "Decode tokens back to text",
                "GET /health": "Health check"
            }
        }
        self.send_json_response(response)
    
    def handle_tokenize(self):
        """Handle tokenization requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            text = data.get('text', '')
            tokenizer_type = data.get('tokenizer_type', 'word')
            
            if not text:
                self.send_error(400, "No text provided")
                return
            
            # Tokenize the text
            start_time = time.time()
            tokens = tokenize_text(text, tokenizer_type)
            end_time = time.time()
            
            response = {
                "success": True,
                "tokens": tokens,
                "original_text": text,
                "tokenizer_type": tokenizer_type,
                "token_count": len(tokens),
                "processing_time_ms": round((end_time - start_time) * 1000, 2),
                "text_length": len(text)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e)
            }
            self.send_json_response(error_response, status=500)
    
    def handle_decode(self):
        """Handle decoding requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            tokens = data.get('tokens', [])
            tokenizer_type = data.get('tokenizer_type', 'word')
            
            if not tokens:
                self.send_error(400, "No tokens provided")
                return
            
            # Reconstruct the text
            start_time = time.time()
            reconstructed = reconstruct_from_tokens(tokens, tokenizer_type)
            end_time = time.time()
            
            response = {
                "success": True,
                "decoded_text": reconstructed,
                "tokenizer_type": tokenizer_type,
                "token_count": len(tokens),
                "processing_time_ms": round((end_time - start_time) * 1000, 2),
                "text_length": len(reconstructed)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e)
            }
            self.send_json_response(error_response, status=500)
    
    def send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def main():
    """Main server function"""
    PORT = 8000
    
    print("🚀 SanTOK Simple HTTP Server")
    print("=" * 40)
    print(f"📡 Starting server on port {PORT}")
    print(f"🌐 Server will be available at: http://localhost:{PORT}")
    print("🔄 Press Ctrl+C to stop the server")
    print("=" * 40)
    
    try:
        with socketserver.TCPServer(("", PORT), SanTOKHandler) as httpd:
            print(f"✅ Server running at http://localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()