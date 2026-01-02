import os
import uuid
import json
import base64
import time
from pathlib import Path
from tornado import web
from jupyter_server.base.handlers import APIHandler

# Create a directory for storing images
IMAGE_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "image_storage")
os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)
print(f"[IMAGE SERVICE] Image storage directory created at: {IMAGE_STORAGE_DIR}")

# Base URL for accessing images
IMAGE_URL_PATH = "/d5m-ai/image-service"


class ImageUploadHandler(APIHandler):
    """Handler for uploading images to the server.

    POST /api/d5m_ai/image-upload
    Request body: JSON with base64 encoded image data
    Response: JSON with image URL and metadata
    """

    @web.authenticated
    async def post(self):
        try:
            print(f"[IMAGE SERVICE] Received image upload request")
            data = self.get_json_body()
            
            if not data or "image_data" not in data:
                self.set_status(400)
                print(f"[IMAGE SERVICE] Error: Missing image data")
                self.finish(json.dumps({"error": "Missing image data"}))
                return
                
            image_data = data["image_data"]
            image_format = data.get("format", "png")
            description = data.get("description", "")
            
            # Log image details (don't log the actual data which could be huge)
            print(f"[IMAGE SERVICE] Processing {image_format} image, description: {description}")
            
            # Check if we have valid base64 data
            data_length = len(image_data) if image_data else 0
            print(f"[IMAGE SERVICE] Received image data of length: {data_length}")
            
            # Remove data URL prefix if present
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
                print(f"[IMAGE SERVICE] Removed data URL prefix")
            
            # Generate unique filename
            timestamp = int(time.time())
            image_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
            filename = f"{image_id}.{image_format}"
            filepath = os.path.join(IMAGE_STORAGE_DIR, filename)
            
            print(f"[IMAGE SERVICE] Generated image ID: {image_id}")
            print(f"[IMAGE SERVICE] Saving to: {filepath}")
            
            # Save the image
            try:
                decoded_data = base64.b64decode(image_data)
                data_size = len(decoded_data)
                
                with open(filepath, "wb") as f:
                    f.write(decoded_data)
                
                file_stat = os.stat(filepath)
                print(f"[IMAGE SERVICE] Image saved successfully: {filename}")
                print(f"[IMAGE SERVICE] File size: {file_stat.st_size} bytes from {data_size} bytes of decoded data")
                
            except Exception as e:
                self.set_status(500)
                print(f"[IMAGE SERVICE] Failed to save image: {str(e)}")
                self.finish(json.dumps({"error": f"Failed to save image: {str(e)}"}))
                return
                
            # Generate URL for accessing the image
            image_url = f"{IMAGE_URL_PATH}/{filename}"
            print(f"[IMAGE SERVICE] Image URL generated: {image_url}")
            
            # Send response
            response = {
                "success": True,
                "image_url": image_url,
                "image_id": image_id,
                "filename": filename,
                "timestamp": timestamp,
                "description": description
            }
            print(f"[IMAGE SERVICE] Sending response: {json.dumps(response)}")
            self.finish(json.dumps(response))
            
        except Exception as e:
            self.set_status(500)
            print(f"[IMAGE SERVICE] Error processing upload: {str(e)}")
            import traceback
            traceback.print_exc()
            self.finish(json.dumps({"error": str(e)}))


class ImageServeHandler(web.StaticFileHandler):
    """Handler for serving images.
    
    GET /d5m-ai/image-service/{filename}
    """
    
    def set_extra_headers(self, path):
        # Allow CORS requests
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        
        # Set cache control for better performance
        self.set_header("Cache-Control", "public, max-age=86400")  # Cache for 24 hours
        
        # Set content type based on file extension
        ext = os.path.splitext(path)[1].lower()
        if ext == '.png':
            self.set_header("Content-Type", "image/png")
        elif ext == '.jpg' or ext == '.jpeg':
            self.set_header("Content-Type", "image/jpeg")
        elif ext == '.gif':
            self.set_header("Content-Type", "image/gif")
        elif ext == '.svg':
            self.set_header("Content-Type", "image/svg+xml")
        
        print(f"[IMAGE SERVICE] Serving file: {path}")
        
    def get(self, path, include_body=True):
        print(f"[IMAGE SERVICE] GET request for image: {path}")
        
        # Check if the file exists before trying to serve it
        full_path = os.path.join(IMAGE_STORAGE_DIR, path)
        if not os.path.exists(full_path):
            print(f"[IMAGE SERVICE] Error: File not found at {full_path}")
            self.set_status(404)
            self.finish(json.dumps({"error": f"Image not found: {path}"}))
            return
            
        if not os.path.isfile(full_path):
            print(f"[IMAGE SERVICE] Error: Path is not a file: {full_path}")
            self.set_status(400)
            self.finish(json.dumps({"error": f"Invalid file path: {path}"}))
            return
        
        try:
            print(f"[IMAGE SERVICE] Attempting to serve file: {full_path}")
            return super().get(path, include_body)
        except Exception as e:
            print(f"[IMAGE SERVICE] Error serving file {path}: {str(e)}")
            import traceback
            traceback.print_exc()
            self.set_status(500)
            self.finish(json.dumps({"error": f"Failed to serve image: {str(e)}"}))
            return


class ImageListHandler(APIHandler):
    """Handler for listing available images.
    
    GET /api/d5m_ai/image-list
    Response: JSON array of image metadata
    """
    
    @web.authenticated
    async def get(self):
        try:
            print(f"[IMAGE SERVICE] Listing images from: {IMAGE_STORAGE_DIR}")
            # Get list of images
            images = []
            for file in os.listdir(IMAGE_STORAGE_DIR):
                if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    file_path = os.path.join(IMAGE_STORAGE_DIR, file)
                    stats = os.stat(file_path)
                    
                    # Extract metadata from filename
                    parts = os.path.splitext(file)[0].split('_')
                    timestamp = parts[0] if len(parts) > 0 else None
                    
                    images.append({
                        "filename": file,
                        "url": f"{IMAGE_URL_PATH}/{file}",
                        "size": stats.st_size,
                        "created": stats.st_ctime,
                        "timestamp": timestamp
                    })
            
            # Sort by creation time (newest first)
            images.sort(key=lambda x: x["created"], reverse=True)
            
            print(f"[IMAGE SERVICE] Found {len(images)} images")
            self.finish(json.dumps({
                "images": images,
                "count": len(images)
            }))
            
        except Exception as e:
            self.set_status(500)
            print(f"[IMAGE SERVICE] Error listing images: {str(e)}")
            self.finish(json.dumps({"error": str(e)}))


class ImageDeleteHandler(APIHandler):
    """Handler for deleting images.
    
    DELETE /api/d5m_ai/image-delete/{filename}
    Response: JSON with success status
    """
    
    @web.authenticated
    async def delete(self, filename):
        try:
            print(f"[IMAGE SERVICE] Delete request for image: {filename}")
            # Sanitize filename to prevent directory traversal
            filename = os.path.basename(filename)
            file_path = os.path.join(IMAGE_STORAGE_DIR, filename)
            
            if not os.path.exists(file_path):
                self.set_status(404)
                print(f"[IMAGE SERVICE] Image not found: {file_path}")
                self.finish(json.dumps({"error": "Image not found"}))
                return
                
            # Delete the file
            os.remove(file_path)
            print(f"[IMAGE SERVICE] Image deleted: {file_path}")
            
            self.finish(json.dumps({
                "success": True,
                "message": f"Image {filename} deleted successfully"
            }))
            
        except Exception as e:
            self.set_status(500)
            print(f"[IMAGE SERVICE] Error deleting image: {str(e)}")
            self.finish(json.dumps({"error": str(e)}))


def get_image_handlers():
    """Returns a list of handlers for the image service."""
    handlers = [
        (r"/api/d5m_ai/image-upload", ImageUploadHandler),
        (r"/api/d5m_ai/image-list", ImageListHandler),
        (r"/api/d5m_ai/image-delete/(.*)", ImageDeleteHandler),
        (f"{IMAGE_URL_PATH}/(.*)", ImageServeHandler, {"path": IMAGE_STORAGE_DIR}),
    ]
    print(f"[IMAGE SERVICE] Registering image handlers: {handlers}")
    return handlers 