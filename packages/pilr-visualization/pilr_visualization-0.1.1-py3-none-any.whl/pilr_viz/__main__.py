"""Main entry point for PILR Visualization CLI"""

import sys
from .app import app

def main():
    """Run the PILR visualization app"""
    print("Starting PILR Visualization...")
    print("Open your browser to http://localhost:8051")
    app.run(debug=False, port=8051, host='0.0.0.0')

if __name__ == '__main__':
    main()
