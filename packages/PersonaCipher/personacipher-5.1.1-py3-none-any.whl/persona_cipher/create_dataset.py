import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import importlib.resources # Added import

# For production, use a user-writable directory.
USER_DATA_BASE_DIR = os.path.join(os.path.expanduser('~'), '.PersonaCipher')
KNOWN_FACES_DIR = os.path.join(USER_DATA_BASE_DIR, 'known_faces')


# Function to fetch image URLs from Google Images
def fetch_image_urls(query, num_images=10):
    query = urllib.parse.quote(query)  # Encode the query for URLs
    url = f"https://www.google.com/search?hl=en&tbm=isch&q={query}"

    # Send a GET request to Google Images
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all image elements
    img_tags = soup.find_all("img")
    img_urls = []

    for img in img_tags:
        img_url = img.get("src")
        if img_url and img_url.startswith("http"):
            img_urls.append(img_url)

        if len(img_urls) >= num_images:
            break

    return img_urls

# Function to download images from URLs
def download_image(url, folder, image_name):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        os.makedirs(folder, exist_ok=True)
        with open(f"{folder}/{image_name}", "wb") as file:
            file.write(response.content)
        print(f"Downloaded {image_name}")
    except Exception as e:
        print(f"Failed to download {image_name}: {e}")

# Function to fetch and save images for a given person
def download_images_for_person(person_name):
    print(f"Searching images for {person_name}...")
    img_urls = fetch_image_urls(person_name)

    folder_name = os.path.join(KNOWN_FACES_DIR, person_name.replace(' ', '_')) # Use the defined KNOWN_FACES_DIR
    image_count = 0

    # Download the first 10 images
    for url in img_urls:
        if image_count >= 10:
            break
        download_image(url, folder_name, f"img{image_count + 1}.jpg")
        image_count += 1

# Function to create the dataset for multiple people
def create_dataset():
    # Debugging prints
    print(f"Current working directory: {os.getcwd()}")
    
    # Construct the path to usernames.txt using importlib.resources
    with importlib.resources.as_file(importlib.resources.files('persona_cipher').joinpath('datasets/usernames.txt')) as usernames_path:
        with open(usernames_path, 'r') as file:
            username_list = [line.strip() for line in file.readlines() if line.strip()]  # Read and clean the usernames

    # Fetch and save images for each username
    for name in username_list:
        download_images_for_person(name)

    print("Dataset creation complete.")

if __name__ == "__main__":
    create_dataset()
