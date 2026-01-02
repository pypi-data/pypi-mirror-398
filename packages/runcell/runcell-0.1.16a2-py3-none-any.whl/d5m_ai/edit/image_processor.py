import os
import time
import uuid
import base64
import json
import re

# Import the image service
from ..image.handler import IMAGE_URL_PATH, IMAGE_STORAGE_DIR


class ImageProcessor:
    def __init__(self, server_url):
        self.server_url = server_url

    async def save_image_directly(self, image_data):
        """
        Save base64 image data directly to the image storage directory.
        """
        try:
            print(f"[HANDLER] Saving image directly to storage")
            print(f"[HANDLER] Image data length: {len(image_data) if image_data else 0}")
            
            # Remove data URL prefix if present
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
                print(f"[HANDLER] Removed data URL prefix")
            
            # Generate unique filename
            timestamp = int(time.time())
            image_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
            filename = f"{image_id}.png"
            filepath = os.path.join(IMAGE_STORAGE_DIR, filename)
            
            print(f"[HANDLER] Generated image ID: {image_id}")
            print(f"[HANDLER] Saving to: {filepath}")
            
            # Save the image
            decoded_data = base64.b64decode(image_data)
            data_size = len(decoded_data)
            
            with open(filepath, "wb") as f:
                f.write(decoded_data)
            
            file_stat = os.stat(filepath)
            print(f"[HANDLER] Image saved successfully: {filename}")
            print(f"[HANDLER] File size: {file_stat.st_size} bytes from {data_size} bytes of decoded data")
            
            # Generate URL for accessing the image
            image_url = f"{self.server_url}{IMAGE_URL_PATH}/{filename}"
            print(f"[HANDLER] Image URL generated: {image_url}")
            
            return image_url
            
        except Exception as e:
            print(f"[HANDLER] Error saving image directly: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def replace_base64_with_urls(self, result):
        """
        Replace base64 image data in result with URLs to the image service.
        """
        try:
            print(f"[HANDLER] Starting to replace base64 with URLs")
            
            # If result is already JSON parsed as a dict
            if isinstance(result, dict):
                print(f"[HANDLER] Processing result as dict")
                if "image/png" in result and result["image/png"]:
                    print(f"[HANDLER] Found image/png in dict, uploading")
                    image_url = await self.save_image_directly(result["image/png"])
                    if image_url:
                        print(f"[HANDLER] Replaced image in dict with URL: {image_url}")
                        # Replace the image/png key with image_url and preserve other keys
                        result_copy = result.copy()
                        del result_copy["image/png"]
                        result_copy["image_url"] = image_url
                        return result_copy
                # Return original dict if no image found
                return result
                
            # If result is a JSON string
            try:
                print(f"[HANDLER] Trying to parse result as JSON")
                result_obj = json.loads(result)
                if isinstance(result_obj, dict):
                    print(f"[HANDLER] Result is a JSON dict")
                    if "image/png" in result_obj and result_obj["image/png"]:
                        print(f"[HANDLER] Found image/png in JSON dict, uploading")
                        image_url = await self.save_image_directly(result_obj["image/png"])
                        if image_url:
                            print(f"[HANDLER] Replaced image in JSON dict with URL: {image_url}")
                            # Replace the image/png key with image_url and preserve other keys
                            result_obj["image_url"] = image_url
                            del result_obj["image/png"]
                            return json.dumps(result_obj)
                    # Return original JSON string if no image found
                    return result
            except json.JSONDecodeError:
                print(f"[HANDLER] Not valid JSON, trying regex replacement")
                # Not valid JSON, try regex replacement
                pass
                
            # Try to replace base64 patterns in the string
            pattern = r'"image\/png":"([^"]+)"'
            print(f"[HANDLER] Looking for image/png patterns with regex")
            
            # We need to handle regex replacement differently for async
            matches = list(re.finditer(pattern, result))
            print(f"[HANDLER] Found {len(matches)} image/png patterns")
            
            new_result = result
            
            for i, match in enumerate(matches):
                base64_data = match.group(1)
                print(f"[HANDLER] Processing match #{i+1}, data length: {len(base64_data)}")
                image_url = await self.save_image_directly(base64_data)
                if image_url:
                    print(f"[HANDLER] Replacing match #{i+1} with URL: {image_url}")
                    # Replace this specific match with the URL
                    new_result = new_result.replace(f'"image/png":"{base64_data}"', f'"image_url":"{image_url}"')
            
            return new_result
            
        except Exception as e:
            print(f"[HANDLER] Error replacing base64 with URLs: {e}")
            import traceback
            traceback.print_exc()
            return result

    async def process_cell_result(self, handler, result):
        """
        Process cell results and handle image data.
        """
        try:
            print(f"[HANDLER] Processing cell result of length: {len(result) if result else 0}")
            
            # Detect image/png data in the result
            if '"image/png"' in result:
                print(f"[HANDLER] Detected image/png data in cell result")
                # Replace base64 data with URLs in the result
                print(f"[HANDLER] Replacing base64 data with URLs in result")
                modified_result = await self.replace_base64_with_urls(result)
                
                # Send the modified result to unblock the function call
                if handler.waiter and not handler.waiter.done():
                    print(f"[HANDLER] Setting modified result to handler.waiter")
                    handler.waiter.set_result(modified_result)
                else:
                    print(f"[HANDLER] Handler waiter not available or already done")
            else:
                print(f"[HANDLER] No image/png data detected in result")
                # No image, just set the result directly
                if handler.waiter and not handler.waiter.done():
                    print(f"[HANDLER] Setting original result to handler.waiter")
                    handler.waiter.set_result(result)
                else:
                    print(f"[HANDLER] Handler waiter not available or already done")
                    
        except Exception as e:
            print(f"[HANDLER] Error processing cell result: {e}")
            import traceback
            traceback.print_exc()
            # Fail safely by returning the original result
            if handler.waiter and not handler.waiter.done():
                print(f"[HANDLER] Error occurred, setting original result to handler.waiter")
                handler.waiter.set_result(result) 