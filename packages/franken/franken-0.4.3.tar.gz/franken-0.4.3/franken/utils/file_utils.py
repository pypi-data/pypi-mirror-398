import hashlib
from pathlib import Path
import requests
from tqdm.auto import tqdm


def compute_md5(file_path):
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(
            lambda: f.read(8192), b""
        ):  # Read in chunks to handle large files
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def validate_file(
    filename: Path, expected_size: int | None = None, expected_md5: str | None = None
) -> bool:
    if expected_md5 is not None:
        actual_md5 = compute_md5(filename)
        if actual_md5 != expected_md5:
            return False
    if expected_size is not None:
        actual_size = filename.stat().st_size
        if expected_size != actual_size:
            return False
    return True


def download_file(
    url: str,
    filename: Path,
    expected_size: int | None = None,
    expected_md5: str | None = None,
    desc: str | None = None,
):
    if (expected_md5 is not None or expected_size is not None) and filename.is_file():
        # Check that the file is correct to avoid re-download
        if validate_file(filename, expected_size, expected_md5):
            return filename

    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get("content-length", 0))
    block_size = 8192
    data_size = 0
    data_md5 = hashlib.md5()
    with (
        open(filename.with_suffix(".temp"), "wb") as file,
        tqdm(
            desc=desc or str(filename),
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar,
    ):
        for chunk in response.iter_content(chunk_size=block_size):
            file.write(chunk)
            data_md5.update(chunk)
            data_size += len(chunk)
            bar.update(len(chunk))
    # validate
    if expected_size is not None and expected_size != data_size:
        raise IOError("Incorrect file size", filename)
    if expected_md5 is not None and data_md5.hexdigest() != expected_md5:
        raise IOError("Incorrect file MD5", filename)

    filename.with_suffix(".temp").replace(filename)
    return filename
