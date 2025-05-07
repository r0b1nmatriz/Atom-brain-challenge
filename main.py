from app import app
import logging
from auth import init_auth

# Set up logging for easier debugging
logging.basicConfig(level=logging.DEBUG)

# Initialize authentication
init_auth(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
