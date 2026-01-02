import os
import time
import uuid
import base64
import json
import re
from ..image.handler import IMAGE_URL_PATH, IMAGE_STORAGE_DIR
from .config import IMAGE_DIR


class ImageProcessor:
    """Handles image processing operations for the JL Agent."""
    
    def __init__(self, connection_id: str, server_url: str):
        self.connection_id = connection_id
        self.server_url = server_url
        self.image_mappings = {}
    
    async def save_image_directly(self, image_data):
        """
        Save base64 image data directly to the image storage directory.
        """
        try:
            print(f"[JL AGENT] Saving image directly to storage")
            print(f"[JL AGENT] Image data length: {len(image_data) if image_data else 0}")
            
            # Remove data URL prefix if present
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
                print(f"[JL AGENT] Removed data URL prefix")
            
            # Generate unique filename
            timestamp = int(time.time())
            image_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
            filename = f"{image_id}.png"
            filepath = os.path.join(IMAGE_STORAGE_DIR, filename)
            
            print(f"[JL AGENT] Generated image ID: {image_id}")
            print(f"[JL AGENT] Saving to: {filepath}")
            
            # Save the image
            decoded_data = base64.b64decode(image_data)
            data_size = len(decoded_data)
            
            with open(filepath, "wb") as f:
                f.write(decoded_data)
            
            file_stat = os.stat(filepath)
            print(f"[JL AGENT] Image saved successfully: {filename}")
            print(f"[JL AGENT] File size: {file_stat.st_size} bytes from {data_size} bytes of decoded data")
            
            # Generate URL for accessing the image
            image_url = f"{self.server_url}{IMAGE_URL_PATH}/{filename}"
            print(f"[JL AGENT] Image URL generated: {image_url}")
            
            return image_url
            
        except Exception as e:
            print(f"[JL AGENT] Error saving image directly: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to local file save if direct save fails
            return await self._save_image_to_file_fallback(image_data)
            
    async def _save_image_to_file_fallback(self, image_data):
        """
        Fallback method to save base64 image data as a local file.
        """
        try:
            # Generate hash of the image data to avoid duplicate files
            image_hash = str(hash(image_data))[:10]  # Use first 10 chars of hash
            image_id = f"{self.connection_id}_{int(time.time())}_{image_hash}"
            filename = f"{image_id}.png"
            filepath = os.path.join(IMAGE_DIR, filename)
            
            print(f"[JL AGENT] Fallback: Saving image to file: {filepath}")
            print(f"[JL AGENT] Fallback: Image data length: {len(image_data) if image_data else 0}")
            
            # Save the image data to file
            with open(filepath, "wb") as f:
                decoded_data = base64.b64decode(image_data)
                f.write(decoded_data)
                print(f"[JL AGENT] Fallback: Wrote {len(decoded_data)} bytes to file")
                
            # Create a URL for accessing the image
            image_url = f"{self.server_url}{IMAGE_URL_PATH}/{filename}"
            
            # Store the mapping for future reference
            self.image_mappings[image_hash] = {
                "filepath": filepath,
                "url": image_url
            }
            
            print(f"[JL AGENT] Fallback: Generated image URL: {image_url}")
            return image_url
            
        except Exception as e:
            print(f"[JL AGENT] Error saving image to file (fallback): {e}")
            import traceback
            traceback.print_exc()
            return None

    async def replace_base64_with_urls(self, result):
        """
        Replace base64 image data in result with URLs to the image service.
        """
        try:
            print(f"[JL AGENT] Starting to replace base64 with URLs")
            
            # If result is already JSON parsed as a dict
            if isinstance(result, dict):
                print(f"[JL AGENT] Processing result as dict")
                if "image/png" in result and result["image/png"]:
                    print(f"[JL AGENT] Found image/png in dict, uploading")
                    image_url = await self.save_image_directly(result["image/png"])
                    if image_url:
                        print(f"[JL AGENT] Replaced image in dict with URL: {image_url}")
                        # Replace the image/png key with image_url and preserve other keys
                        result_copy = result.copy()
                        del result_copy["image/png"]
                        result_copy["image_url"] = image_url
                        return result_copy
                # Return original dict if no image found
                return result
                
            # If result is a JSON string
            try:
                print(f"[JL AGENT] Trying to parse result as JSON")
                result_obj = json.loads(result)
                if isinstance(result_obj, dict):
                    print(f"[JL AGENT] Result is a JSON dict")
                    if "image/png" in result_obj and result_obj["image/png"]:
                        print(f"[JL AGENT] Found image/png in JSON dict, uploading")
                        image_url = await self.save_image_directly(result_obj["image/png"])
                        if image_url:
                            print(f"[JL AGENT] Replaced image in JSON dict with URL: {image_url}")
                            # Replace the image/png key with image_url and preserve other keys
                            result_obj["image_url"] = image_url
                            del result_obj["image/png"]
                            return json.dumps(result_obj)
                    # Return original JSON string if no image found
                    return result
            except json.JSONDecodeError:
                print(f"[JL AGENT] Not valid JSON, trying regex replacement")
                # Not valid JSON, try regex replacement
                pass
                
            # Try to replace base64 patterns in the string
            pattern = r'"image\/png":"([^"]+)"'
            print(f"[JL AGENT] Looking for image/png patterns with regex")
            
            # We need to handle regex replacement differently for async
            matches = list(re.finditer(pattern, result))
            print(f"[JL AGENT] Found {len(matches)} image/png patterns")
            
            new_result = result
            
            for i, match in enumerate(matches):
                base64_data = match.group(1)
                print(f"[JL AGENT] Processing match #{i+1}, data length: {len(base64_data)}")
                image_url = await self.save_image_directly(base64_data)
                if image_url:
                    print(f"[JL AGENT] Replacing match #{i+1} with URL: {image_url}")
                    # Replace this specific match with the URL
                    new_result = new_result.replace(f'"image/png":"{base64_data}"', f'"image_url":"{image_url}"')
            
            return new_result
            
        except Exception as e:
            print(f"[JL AGENT] Error replacing base64 with URLs: {e}")
            import traceback
            traceback.print_exc()
            return result

    def cleanup_images(self):
        """Clean up any temporary image files for this connection."""
        for image_info in self.image_mappings.values():
            try:
                if os.path.exists(image_info["filepath"]):
                    os.remove(image_info["filepath"])
            except Exception as e:
                print(f"Error removing temporary image file: {e}") 