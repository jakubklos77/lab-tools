# Usage: main.sh
# rename files based on EXIF data and filename patterns

import os
import re
import subprocess

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
    for file_name in os.listdir("."):
        if file_name.endswith('.JPG'):
            base = os.path.splitext(file_name)[0]
            new_name = f"{base}.jpg"
            try:
                os.rename(file_name, new_name)
                print(f"Renamed {file_name} -> {new_name}")
            except Exception as e:
                print(f"Error renaming {file_name}: {e}")


def convert_heic_to_jpg():
    if not HEIC_SUPPORT:
        print("Skipping HEIC conversion - pillow-heif not available")
        return

    for file_name in os.listdir("."):
        if not file_name.lower().endswith(('.heic', '.heif')):
            continue

        base = os.path.splitext(file_name)[0]
        output_name = f"{base}.jpg"

        try:
            print(f"Converting {file_name} -> {output_name}")
            with Image.open(file_name) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output_name, 'JPEG', quality=95, exif=img.info.get('exif'))

            if os.path.exists(output_name) and os.path.getsize(output_name) > 0:
                os.remove(file_name)
                print(f"Removed original: {file_name}")
            else:
                print(f"Error: {output_name} was not created properly")

        except Exception as e:
            print(f"Error converting {file_name}: {e}")
            if os.path.exists(output_name):
                os.remove(output_name)


def normalize_filename(date_str, time_str="000000"):
    base = f"IMG_{date_str}_{time_str}"
    name = f"{base}.jpg"
    counter = 1
    while os.path.exists(name):
        name = f"{base}_{counter}.jpg"
        counter += 1
    return name


def inject_date_from_filename():
    """Write EXIF date tags for files with corrupt EXIF, parsing the date from the filename.

    Handles filenames like 200706250912_IMG_3080.jpg (YYYYMMDDHHMM_*.jpg)
    where continuous digits encode date+time without a separator.
    Uses -m (ignore minor errors) and -F (fix bad IFD offsets) to allow
    writes to files that exiftool would otherwise refuse to touch.
    """
    pattern = re.compile(r'^(\d{8})(\d{4,6})_.*\.jpg$', re.IGNORECASE)
    for file_name in os.listdir("."):
        m = pattern.match(file_name)
        if not m:
            continue
        date_str = m.group(1)
        time_str = m.group(2).ljust(6, '0')[:6]
        dt = f"{date_str[:4]}:{date_str[4:6]}:{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        result = subprocess.run(
            ["exiftool", "-overwrite_original", "-m", "-F",
             f"-DateTimeOriginal={dt}", f"-CreateDate={dt}", file_name],
            capture_output=True, text=True,
        )
        if "1 image files updated" in result.stdout:
            print(f"Injected EXIF date {dt} into {file_name}")
        elif result.stderr.strip():
            print(f"Could not inject date into {file_name}: {result.stderr.strip()}")


def rename_based_on_exif():
    # DateTimeOriginal first so CreateDate (more reliable) wins when both exist
    subprocess.run([
        "exiftool", "-m",
        "-FileName<DateTimeOriginal",
        "-FileName<CreateDate",
        "-d", "IMG_%Y%m%d_%H%M%S%%-c.%%le",
        "."
    ])


def rename_files_without_exif():
    for file_name in os.listdir("."):
        if re.match(r"IMG_\d{8}_\d{6}", file_name):
            continue

        date_str = time_str = None

        if m := re.match(r"IMG-(\d{8})-WA\d+\.jpg$", file_name, re.IGNORECASE):
            date_str, time_str = m.group(1), "000000"

        elif m := re.match(r"(\d{8})_(\d{6})\d+\.jpg$", file_name, re.IGNORECASE):
            date_str, time_str = m.group(1), m.group(2)

        elif m := re.match(
            r"Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2}).*\.jpg$",
            file_name, re.IGNORECASE,
        ):
            date_str = m.group(1) + m.group(2) + m.group(3)
            time_str = m.group(4) + m.group(5) + m.group(6)

        elif m := re.match(r"InCollage_(\d{8})_(\d{6})\d+\.jpg$", file_name, re.IGNORECASE):
            date_str, time_str = m.group(1), m.group(2)

        if date_str:
            new_name = normalize_filename(date_str, time_str)
            print(f"Renaming {file_name} -> {new_name}")
            os.rename(file_name, new_name)


def guess_folder_date():
    """Extract year and month from the current directory name.

    Handles:
      2004/2004-02-ValdiFiemme  → ('2004', '02')
      2004/2004-02 ValdiFiemme  → ('2004', '02')
      2004/02-ValdiFiemme       → ('2004', '02')  (year from parent dir)
      2004/02 ValdiFiemme       → ('2004', '02')  (year from parent dir)
    """
    cwd = os.getcwd()
    folder = os.path.basename(cwd)

    # YYYY-MM followed by dash, space, or end of string
    m = re.match(r'^(\d{4})-(\d{2})(?:[-\s]|$)', folder)
    if m:
        return m.group(1), m.group(2)

    # MM followed by dash or space; get year from the parent directory name
    m = re.match(r'^(\d{2})[-\s]', folder)
    if m:
        parent = os.path.basename(os.path.dirname(cwd))
        if re.match(r'^\d{4}$', parent):
            return parent, m.group(1)

    return None, None


def inject_date_from_folder():
    """For files with no parseable date, guess year/month from the folder name and use day 01."""
    year, month = guess_folder_date()
    if not year:
        return

    unprocessed = sorted(
        f for f in os.listdir(".")
        if f.lower().endswith('.jpg') and not re.match(r'IMG_\d{8}_\d{6}', f)
    )
    if not unprocessed:
        return

    date_str = f"{year}{month}01"
    dt = f"{year}:{month}:01 00:00:00"
    print(f"\nUsing folder-guessed date {year}-{month}-01 for {len(unprocessed)} file(s):")

    for file_name in unprocessed:
        result = subprocess.run(
            ["exiftool", "-overwrite_original", "-m", "-F",
             f"-DateTimeOriginal={dt}", f"-CreateDate={dt}", file_name],
            capture_output=True, text=True,
        )
        if "1 image files updated" in result.stdout:
            new_name = normalize_filename(date_str)
            os.rename(file_name, new_name)
            print(f"  {file_name} -> {new_name}")
        else:
            err = result.stderr.strip()
            print(f"  Could not process {file_name}" + (f": {err}" if err else ""))


def report_unprocessed():
    skipped = [
        f for f in os.listdir(".")
        if f.lower().endswith('.jpg') and not re.match(r"IMG_\d{8}_\d{6}", f)
    ]
    if skipped:
        print("\nFiles with no usable date — rename manually:")
        for f in sorted(skipped):
            print(f"  {f}")


def main():
    convert_jpg_uppercase_to_lowercase()
    convert_heic_to_jpg()
    inject_date_from_filename()
    rename_based_on_exif()
    rename_files_without_exif()
    inject_date_from_folder()
    report_unprocessed()


if __name__ == "__main__":
    main()
