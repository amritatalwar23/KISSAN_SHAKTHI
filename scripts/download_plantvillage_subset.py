"""Download and organize PlantVillage dataset subset for Kisan Shakti.

Streams the Mendeley archive (827.8 MB) with automatic retry and resumption,
verifies zipfile integrity, extracts up to 1,000 images per target class into
data/plantvillage/<class_name>/, and cleans up the temporary archive when done.
"""

import os
import sys
import zipfile
import shutil
import time
from pathlib import Path
import requests

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "plantvillage"
TEMP_ZIP = PROJECT_ROOT / "data" / "plantvillage_temp.zip"

MENDELEY_URL = (
    "https://data.mendeley.com/public-files/datasets/tywbtsjrjv/files/"
    "d5652a28-c1d8-4b76-97f3-72fb80f94efc/file_downloaded"
)

TARGET_CLASSES = [
    # Tomato (10 classes)
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
    # Potato (3 classes)
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    # Corn / Maize (4 classes)
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy"
]

MAX_PER_CLASS = 1000

def get_remote_total_size(url, headers):
    try:
        resp = requests.head(url, headers=headers, allow_redirects=True, timeout=20)
        return int(resp.headers.get("Content-Length", 0))
    except Exception as e:
        print(f"Warning: could not get Content-Length from HEAD ({e}), using default ~828MB")
        return 868032562

def download_with_auto_resume(url, dest_path, max_retries=30):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    total_size = get_remote_total_size(url, base_headers)
    print(f"Target archive size: {total_size / (1024*1024):.1f} MB")
    
    # Check if already fully downloaded
    if dest_path.exists():
        cur_sz = dest_path.stat().st_size
        if cur_sz == total_size and zipfile.is_zipfile(dest_path):
            print(f"Archive is already fully downloaded ({cur_sz / (1024*1024):.1f} MB) and verified.")
            return

    retry_count = 0
    while retry_count < max_retries:
        downloaded = dest_path.stat().st_size if dest_path.exists() else 0
        if total_size > 0 and downloaded >= total_size:
            print(f"All {downloaded / (1024*1024):.1f} MB downloaded.")
            if zipfile.is_zipfile(dest_path):
                print("Zip integrity verified successfully!")
                return
            else:
                print("File size reached but zip verification failed. Re-starting download...")
                dest_path.unlink(missing_ok=True)
                downloaded = 0

        headers = dict(base_headers)
        mode = "wb"
        if downloaded > 0:
            headers["Range"] = f"bytes={downloaded}-"
            mode = "ab"
            pct = (downloaded / total_size * 100) if total_size > 0 else 0
            print(f"\n[Attempt {retry_count+1}/{max_retries}] Resuming from {downloaded / (1024*1024):.1f} MB ({pct:.1f}%)...")
        else:
            print(f"\n[Attempt {retry_count+1}/{max_retries}] Starting download from beginning...")

        try:
            with requests.get(url, headers=headers, stream=True, timeout=25) as resp:
                if resp.status_code not in (200, 206):
                    print(f"Server returned status {resp.status_code}, waiting to retry...")
                    time.sleep(3)
                    retry_count += 1
                    continue

                chunk_size = 1024 * 1024 # 1 MB chunks
                last_log = time.time()
                with open(dest_path, mode) as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if time.time() - last_log >= 5:
                                pct = (downloaded / total_size * 100) if total_size > 0 else 0
                                print(f"Progress: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({pct:.1f}%)")
                                last_log = time.time()

            # If loop finished normally
            if dest_path.exists() and zipfile.is_zipfile(dest_path):
                print(f"\nDownload completed and zip verified: {dest_path.stat().st_size / (1024*1024):.1f} MB")
                return

        except (requests.exceptions.RequestException, TimeoutError, ConnectionError, OSError) as e:
            print(f"Connection interrupted ({type(e).__name__}). Reconnecting in 3 seconds...")
            time.sleep(3)
            retry_count += 1

    if not (dest_path.exists() and zipfile.is_zipfile(dest_path)):
        raise RuntimeError(f"Failed to complete download after {max_retries} attempts.")

def extract_and_organize():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nExtracting images from {TEMP_ZIP.name}...")
    
    with zipfile.ZipFile(TEMP_ZIP, "r") as zf:
        members = zf.namelist()
        print(f"Archive contents: {len(members)} entries found.")
        
        class_counts = {c: 0 for c in TARGET_CLASSES}
        
        # Ensure folders exist
        for c in TARGET_CLASSES:
            (DATA_DIR / c).mkdir(parents=True, exist_ok=True)
            # Count existing files if any
            class_counts[c] = len(list((DATA_DIR / c).glob("*.jpg")) + list((DATA_DIR / c).glob("*.png")) + list((DATA_DIR / c).glob("*.JPG")))

        print(f"Filtering and saving up to {MAX_PER_CLASS} images per target class...")
        for member in members:
            if member.endswith("/") or not member.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
                
            parts = member.replace("\\", "/").split("/")
            if len(parts) >= 2:
                folder_name = parts[-2].strip()
                filename = parts[-1].strip()
                
                for target_class in TARGET_CLASSES:
                    if folder_name.lower() == target_class.lower() or folder_name.replace(" ", "_").lower() == target_class.replace(" ", "_").lower():
                        if class_counts[target_class] < MAX_PER_CLASS:
                            dest_file = DATA_DIR / target_class / filename
                            if not dest_file.exists():
                                with zf.open(member) as src, open(dest_file, "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                                class_counts[target_class] += 1
                        break

    print("\n" + "=" * 65)
    print(f"{'Class Name':<45} | {'Images Saved':<12}")
    print("=" * 65)
    total_saved = 0
    for c in TARGET_CLASSES:
        cnt = class_counts[c]
        total_saved += cnt
        print(f"{c:<45} | {cnt:<12}")
    print("=" * 65)
    print(f"Total dataset images organized: {total_saved}")
    print(f"Destination: {DATA_DIR}")

def cleanup():
    if TEMP_ZIP.exists():
        print(f"\nCleaning up temporary archive {TEMP_ZIP.name} to preserve free disk space...")
        try:
            TEMP_ZIP.unlink()
            print("Temporary archive deleted successfully.")
        except Exception as e:
            print(f"Note: Could not delete temp zip: {e}")

if __name__ == "__main__":
    download_with_auto_resume(MENDELEY_URL, TEMP_ZIP, max_retries=30)
    extract_and_organize()
    cleanup()
