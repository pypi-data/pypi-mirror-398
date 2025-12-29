import os
import requests
from concurrent.futures import ThreadPoolExecutor

def download_image(url, output_dir):
    try:
        filename = url.split("/")[-1].split("?")[0]
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            print(f"[SKIP] {filename} already exists.")
            return
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"[OK] Downloaded {filename}")
    except Exception as e:
        print(f"[FAIL] {url} - {e}")

def download_images_from_txt(txt_file, output_dir="images", max_workers=8):
    # Try to extract subreddit from txt filename: images_<subreddit>_TIMESTAMP.txt
    base = os.path.basename(txt_file)
    subreddit = None
    if base.startswith("images_") and "_" in base:
        parts = base.split("_")
        if len(parts) > 2:
            subreddit = parts[1]
    # Download to images/<subreddit> if possible
    if subreddit:
        output_dir = os.path.join(output_dir, subreddit)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(txt_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(lambda url: download_image(url, output_dir), urls)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download images from a list of URLs in a txt file.")
    parser.add_argument("txt_file", type=str, help="Path to the txt file containing image URLs (one per line)")
    parser.add_argument("--output-dir", type=str, default="images", help="Directory to save images")
    parser.add_argument("--max-workers", type=int, default=8, help="Number of parallel downloads")
    args = parser.parse_args()
    download_images_from_txt(args.txt_file, args.output_dir, args.max_workers)
