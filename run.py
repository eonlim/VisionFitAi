import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Now import and run the app
from app import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)