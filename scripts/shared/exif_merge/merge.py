# Usage: ./exif_photo_filename_merge.py
# rename files based on EXIF data and filename patterns

import os
import re
import subprocess
from datetime import datetime

# Try to import pillow-heif for HEIC conversion
try:
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False
    print("Warning: pillow-heif not installed. HEIC conversion will be skipped.")
    print("To install: pip install pillow-heif")

def convert_jpg_uppercase_to_lowercase():
    """Convert all .JPG files to .jpg (lowercase extension)."""
    for file_name in os.listdir("."):
        if file_name.endswith('.JPG'):
            # Generate new filename with lowercase extension
            base_name = os.path.splitext(file_name)[0]
            new_name = f"{base_name}.jpg"

            try:
                print(f"Renaming {file_name} to {new_name}")
                os.rename(file_name, new_name)
            except Exception as e:
                print(f"Error renaming {file_name}: {e}")

def convert_heic_to_jpg():
    """Convert all HEIC files to JPG format while preserving EXIF data."""
    if not HEIC_SUPPORT:
        print("Skipping HEIC conversion - pillow-heif not available")
        return

    for file_name in os.listdir("."):
        if file_name.lower().endswith(('.heic', '.heif')):
            # Generate output filename by replacing extension with lowercase .jpg
            base_name = os.path.splitext(file_name)[0]
            output_name = f"{base_name}.jpg"

            try:
                print(f"Converting {file_name} to {output_name} using pillow-heif")

                # Open HEIC file with pillow-heif
                with Image.open(file_name) as img:
                    # Convert to RGB if necessary (HEIC might be in different color space)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Save as JPG with high quality, preserving EXIF
                    img.save(output_name, 'JPEG', quality=95, exif=img.info.get('exif'))

                # Verify the output file was created successfully
                if os.path.exists(output_name) and os.path.getsize(output_name) > 0:
                    # Remove the original HEIC file after successful conversion
                    os.remove(file_name)
                    print(f"Successfully converted and removed original file: {file_name}")
                else:
                    print(f"Error: Output file {output_name} was not created properly")

            except Exception as e:
                print(f"Error converting {file_name}: {e}")
                # Clean up any partial output file
                if os.path.exists(output_name):
                    os.remove(output_name)

def normalize_filename(file_name, date_str, time_str="000000"):
    """Generate the normalized filename based on date and time."""
    new_name = f"IMG_{date_str}_{time_str}"
    counter = 1
    while os.path.exists(f"{new_name}.jpg"):
        new_name = f"IMG_{date_str}_{time_str}_{counter}"
        counter += 1
    return f"{new_name}.jpg"

def rename_based_on_exif():
    """Run exiftool to rename files based on EXIF data."""
    exif_command = [
        "exiftool", '-FileName<CreateDate', '-d', "IMG_%Y%m%d_%H%M%S%%-c.%%le", "."
    ]
    subprocess.run(exif_command)

def rename_files_without_exif():
    """Rename files without EXIF data using their filenames."""
    for file_name in os.listdir("."):
        if not re.match(r"IMG_\d{8}_\d{6}", file_name):
            date_str, time_str = None, None

            # Check if file name matches the pattern: IMG-YYYYMMDD-WAxxxx.jpg or .JPG
            match = re.match(r"IMG-(\d{8})-WA\d+\.(jpg|JPG)", file_name)
            if match:
                date_str = match.group(1)
                time_str = "000000"

            # Check if file name matches the pattern: 20241201_120118921.jpg or .JPG
            match = re.match(r"(\d{8})_(\d{6})\d+\.(jpg|JPG)", file_name)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)

            # Check if file name matches the pattern: Screenshot_2024-12-04-09-04-05-49_1c337646f29875672b5a61192b9010f9_1.jpg or .JPG
            match = re.match(r"Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2}).*\.(jpg|JPG)", file_name)
            if match:
                date_str = match.group(1) + match.group(2) + match.group(3)
                time_str = match.group(4) + match.group(5) + match.group(6)

            # Check if file name matches the pattern: InCollage_YYYYMMDD_HHMMSSxxxx.jpg or .JPG
            match = re.match(r"InCollage_(\d{8})_(\d{6})\d+\.(jpg|JPG)", file_name)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)

            # If a date was found, rename the file
            if date_str:
                new_name = normalize_filename(file_name, date_str, time_str)
                print(f"Renaming {file_name} to {new_name}")
                os.rename(file_name, new_name)

def main():
    # Step 1: Convert .JPG files to .jpg (lowercase extension)
    convert_jpg_uppercase_to_lowercase()
    # Step 2: Convert HEIC files to JPG while preserving EXIF data
    convert_heic_to_jpg()
    # Step 3: Rename files based on EXIF data
    rename_based_on_exif()
    # Step 4: Rename remaining files based on filename patterns
    rename_files_without_exif()

if __name__ == "__main__":
    main()