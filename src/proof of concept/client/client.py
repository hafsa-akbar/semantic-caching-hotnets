import requests
import base64
import os
import json
from PIL import Image
import shutil
import time

CACHE_DIR = 'cache'
CACHE_METADATA_FILE = 'cache/cache_metadata.json'

def load_cache_metadata():
    if os.path.exists(CACHE_METADATA_FILE):
        with open(CACHE_METADATA_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    return []

cache_metadata = load_cache_metadata()

def save_cache_metadata(metadata):
    with open(CACHE_METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

def clear_cache():
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR)
    save_cache_metadata([])

    global cache_metadata
    cache_metadata = []

def save_image_to_cache(image_data):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    image_path = os.path.join(CACHE_DIR, f"{image_data['id']}.jpg")
    
    with open(image_path, "wb") as img_file:
        img_file.write(base64.b64decode(image_data["image_data"]))

    cache_metadata.append({
        "id": image_data["id"],
        "category": image_data["category"]
    })
    save_cache_metadata(cache_metadata)

def compute_image_size(image_data):
    return len(base64.b64decode(image_data)) if image_data else 0

def get_cached_images_by_category(category):
    return [img['id'] for img in cache_metadata if img['category'] == category]

def request_category(image_id):
    response = requests.get(f"http://127.0.0.1:5000/category/{image_id}")
    if response.ok:
        return response.text
    return None

def request_image(image_id, simple_cache, t):
    category = request_category(image_id)
    if not category:
        return None
    
    cached_images = [] if simple_cache else get_cached_images_by_category(category)
    params = {
        'category': category,
        'threshold': t,
        'cached_images': cached_images
    }
    response = requests.get(f"http://127.0.0.1:5000/image/{image_id}", params=params)
    return response.json()

def display_image(image_id):
    image_path = os.path.join(CACHE_DIR, f"{image_id}.jpg")
    if os.path.exists(image_path):
        img = Image.open(image_path)
        img.show()

def get_image(image_id, simple_cache=False, t=1, display=True):
    bytes_downloaded = 0
    cached_image = next((img for img in cache_metadata if img['id'] == image_id), None)

    if not cached_image:
        server_response = request_image(image_id, simple_cache, t)

        if 'reuse_similar' in server_response:
            cached_image_id = server_response['reuse_similar']
            print(f'USING CACHED IMAGE {cached_image_id}')
            image_id = cached_image_id 
        elif 'image_data' in server_response:
            save_image_to_cache(server_response)
            bytes_downloaded += compute_image_size(server_response['image_data'])

    if display:
        display_image(image_id)
    time.sleep(0.1)
    return bytes_downloaded
    
if __name__ == "__main__":
    image_id = "image_1260"
    bytes_downloaded = get_image(image_id, simple_cache=False, t=1, display=False)