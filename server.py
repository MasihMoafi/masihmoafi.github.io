#!/usr/bin/env python3
import os
import json
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8091

class CustomRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow CORS for development if needed
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/upload-image':
            try:
                content_length = int(self.headers['Content-Length'])
                filename = self.headers.get('X-Filename', 'upload.png').strip()
                filename = os.path.basename(filename) # prevent traversal
                
                # Make sure visuals directory exists
                os.makedirs('visuals', exist_ok=True)
                
                filepath = os.path.join('visuals', filename)
                
                # Read binary file body
                image_data = self.rfile.read(content_length)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                    
                print(f"Saved uploaded image to {filepath}")
                
                response_data = {
                    'status': 'success',
                    'url': f'visuals/{filename}'
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                print(f"Error uploading image: {e}")
                self.send_error_response(500, str(e))
        elif self.path == '/api/save-post':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                
                filename = data.get('filename', '').strip()
                title = data.get('title', '').strip()
                meta = data.get('meta', '').strip()
                content = data.get('content', '')
                
                if not filename or not title:
                    self.send_error_response(400, "Filename and Title are required.")
                    return
                
                # Enforce safety guardrails on filename
                if not filename.endswith('.md'):
                    filename += '.md'
                filename = os.path.basename(filename) # prevent directory traversal
                
                # Format full Jekyll Markdown content
                full_md = f"---\nlayout: post\ntitle: \"{title}\"\nmeta: \"{meta}\"\n---\n\n{content}"
                
                # Write to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_md)
                
                print(f"Saved raw markdown to {filename}")
                
                # Recompile the site using build.py
                print("Rebuilding static site...")
                result = subprocess.run(['python3', 'build.py'], capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                
                slug = filename[:-3]
                response_data = {
                    'status': 'success',
                    'message': f'Post saved and site rebuilt successfully!',
                    'url': f'{slug}.html'
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
            except Exception as e:
                print(f"Error saving post: {e}")
                self.send_error_response(500, str(e))
        else:
            self.send_response(404)
            self.end_headers()

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'error', 'message': message}).encode('utf-8'))

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, CustomRequestHandler)
    print(f"Serving local CMS server at http://127.0.0.1:{PORT}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
