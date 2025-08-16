import json
import requests
from pathlib import Path

# --- CONFIGURATION: YOU MUST EDIT THESE TWO VALUES ---
YOUR_API_ENDPOINT = "https://api.yoursite.com/v1/images"  # <-- REPLACE THIS
YOUR_API_TOKEN = "your_secret_bearer_token_here"            # <-- REPLACE THIS
# ----------------------------------------------------

# Directory where your transformed JSON files are located
TRANSFORMED_DATA_DIR = Path("output/transformed_data")

def migrate_image(image_url: str) -> str | None:
    """
    Downloads an image from a URL, uploads it to your system,
    and returns the new URL.
    """
    if not image_url or not image_url.startswith('http'):
        print("     -> Skipping invalid or missing URL.")
        return None

    try:
        # --- Step 1: Download the original image ---
        print(f"     -> Downloading: {image_url[:60]}...")
        response = requests.get(image_url, timeout=20)
        response.raise_for_status()
        image_content = response.content

        # --- Step 2: Upload the image to your system ---
        headers = {"Authorization": f"Bearer {YOUR_API_TOKEN}"}
        # The 'files' dict tells requests to send a multipart/form-data upload
        files = {"image_file": ("image.jpg", image_content)}
        
        print("        ...Uploading to your system...")
        upload_response = requests.post(YOUR_API_ENDPOINT, headers=headers, files=files, timeout=30)
        upload_response.raise_for_status()

        # --- Step 3: Get the new URL from your API's response ---
        # We assume your API returns a JSON like {"url": "https://.../new_image.jpg"}
        new_url = upload_response.json().get("url")
        if not new_url:
            print("        ERROR: New URL not found in API response.")
            return None
            
        print(f"        Success! New URL: {new_url}")
        return new_url

    except requests.exceptions.RequestException as e:
        print(f"        ERROR migrating image: {e}")
        return None
    except json.JSONDecodeError:
        print("        ERROR: Could not decode JSON response from your API.")
        return None

def process_all_files():
    """
    Main function to find all transformed files, process their images,
    and save the updated files.
    """
    print("🚀 Starting Image Migration Process...")
    if not TRANSFORMED_DATA_DIR.exists():
        print(f"Error: Directory not found: {TRANSFORMED_DATA_DIR}")
        return

    # Find all transformed JSON files in the directory
    files_to_process = list(TRANSFORMED_DATA_DIR.glob("*_transformed.json"))
    if not files_to_process:
        print("No transformed files found to process.")
        return
        
    print(f"Found {len(files_to_process)} files to process.")

    for file_path in files_to_process:
        print(f"\n=============================================")
        print(f"Processing file: {file_path.name}")
        
        with file_path.open('r+', encoding='utf-8') as f:
            menu_data = json.load(f)
            
            # Iterate through every item in every category
            for category in menu_data.get("categories", []):
                print(f"  Scanning category: {category.get('name')}")
                for item in category.get("items", []):
                    original_url = item.get("original_image_url")
                    
                    if original_url:
                        # Migrate the image and get the new URL
                        new_image_url = migrate_image(original_url)
                        # Update the 'image' field with the new URL
                        item["image"] = new_image_url
                    
                    # Clean up the temporary field
                    if "original_image_url" in item:
                        del item["original_image_url"]

            # Go back to the beginning of the file to overwrite it
            f.seek(0)
            # Write the updated data back to the same file
            json.dump(menu_data, f, indent=2, ensure_ascii=False)
            f.truncate()
            print(f"  ✅ Finished processing and saved updates to {file_path.name}")

    print("\n\n🎉 All image migrations finished successfully!")

if __name__ == "__main__":
    process_all_files()