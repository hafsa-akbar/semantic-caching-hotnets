import os
import random
import csv
from client import get_image, clear_cache

SERVER_IMAGE_DIR = '../server/images'
LOG_FILE = 'simulation.csv'
NUM_CLIENTS = 100  # Repeat process 100 times

def get_all_websites_and_categories(server_image_dir):
    website_folders = []
    for website in os.listdir(server_image_dir):
        website_path = os.path.join(server_image_dir, website)
        if os.path.isdir(website_path):
            website_folders.append(website_path)
    return website_folders

def get_images_from_category(website_path):
    image_ids = []
    for category in os.listdir(website_path):
        category_path = os.path.join(website_path, category)
        if os.path.isdir(category_path):
            for image_file in os.listdir(category_path):
                if image_file.endswith('.jpg'):
                    image_id = image_file.replace('.jpg', '')
                    image_ids.append(image_id)
    return image_ids

def pick_random_websites(website_folders, num_websites):
    return random.sample(website_folders, num_websites)

def pick_random_images(image_ids, num_images=30):
    return random.choices(image_ids, k=num_images)

def process_images(image_list, simple_cache):
    clear_cache()
    total_download_bytes = 0
    for image_id in image_list:
        total_download_bytes += get_image(image_id, simple_cache=simple_cache, display=False)
    return total_download_bytes

def log_results(csv_writer, csv_file, list_index, X, Y, simple_cache_bytes, similarity_cache_bytes, client_id):
    csv_writer.writerow({
        'Client ID': client_id + 1,
        'List Index': list_index + 1,
        'Number of Websites (FW)': X,
        'Number of Images (AC)': Y,
        'Simple Cache (KB)': f"{simple_cache_bytes / 1024:.2f}",
        'Similarity Cache (KB)': f"{similarity_cache_bytes / 1024:.2f}"
    })
    csv_file.flush()  # Flush after each write to log immediately

def download_and_log_images(server_image_dir, log_file, X_values, Y_values):
    website_folders = get_all_websites_and_categories(server_image_dir)

    with open(log_file, 'w', newline='') as csv_file:
        fieldnames = ['Client ID', 'List Index', 'Number of Websites (FW)', 'Number of Images (AC)', 
                      'Simple Cache (KB)', 'Similarity Cache (KB)']
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()

        list_index = 0
        for X in X_values:
            for Y in Y_values:
                for client_id in range(NUM_CLIENTS):  # Simulate 100 pseudo-clients
                    selected_websites = pick_random_websites(website_folders, X)

                    image_list = []

                    for website_path in selected_websites:
                        image_list.extend(get_images_from_category(website_path))

                    random_articles = pick_random_images(image_list, num_images=Y)

                    similarity_cache_bytes = process_images(random_articles, simple_cache=False)
                    simple_cache_bytes = process_images(random_articles, simple_cache=True)

                    log_results(csv_writer, csv_file, list_index, X, Y, simple_cache_bytes, similarity_cache_bytes, client_id)

                list_index += 1

    clear_cache()

if __name__ == "__main__":
    websites = [1, 2, 3, 4, 5]  # Number of websites (FW) to test
    images = [10, 20, 30, 40]   # Number of images (AC) to test
    download_and_log_images(SERVER_IMAGE_DIR, LOG_FILE, websites, images)
