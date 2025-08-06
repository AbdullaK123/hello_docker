# app.py
from flask import Flask
import os
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = socket.gethostname()
    app_name = os.environ.get('APP_NAME', 'Docker App')
    version = os.environ.get('APP_VERSION', '1.0')
    environment = os.environ.get('ENV', 'development')
    
    return f"""
    <h1>Hello from {app_name}!</h1>
    <p><strong>Version:</strong> {version}</p>
    <p><strong>Environment:</strong> {environment}</p>
    <p><strong>Container hostname:</strong> {hostname}</p>
    <p><strong>Python version:</strong> {os.sys.version.split()[0]}</p>
    """

@app.route('/health')
def health():
    return {
        "status": "healthy", 
        "container": socket.gethostname(),
        "app": os.environ.get('APP_NAME', 'Docker App'),
        "version": os.environ.get('APP_VERSION', '1.0')
    }

if __name__ == '__main__':
    debug_mode = os.environ.get('ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)