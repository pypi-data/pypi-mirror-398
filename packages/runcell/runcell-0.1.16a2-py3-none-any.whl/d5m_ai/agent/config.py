import os

# Global registry so the front-end can route `cell_result` messages back to
# the correct handler instance.
handler_registry = {}

# Directory for storing temporary image files
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Create a base URL for serving images
IMAGE_BASE_URL = "/d5m-ai/images"  # This should match your server's route configuration 