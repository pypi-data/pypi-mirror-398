#!/usr/bin/env python3
"""
utils.py

Helpers shared by ingest tools: download with safety checks, and GPG symmetric
encryption for DB files.
"""
import shutil
import os
from urllib.request import Request, urlopen
import time
import subprocess


def safe_download(url, dest_path, max_bytes=50_000_000, timeout=30):
    """Download with simple safety checks: user-agent, max size, timeout.
    Returns path to downloaded file.
    """
    req = Request(url, headers={"User-Agent": "OlhoDeDeus-Scraper/1.0"})
    start = time.time()
    with urlopen(req, timeout=timeout) as resp:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        total = 0
        with open(dest_path, "wb") as out:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                out.write(chunk)
                total += len(chunk)
                if total > max_bytes:
                    out.close()
                    raise IOError(f"Downloaded size exceeded max_bytes ({max_bytes})")
                if time.time() - start > timeout:
                    raise IOError("Download timeout")
    return dest_path


def encrypt_file_gpg_symmetric(input_path, output_path=None, cipher_algo="AES256"):
    if output_path is None:
        output_path = input_path + ".gpg"
    cmd = ["gpg", "--batch", "--yes", "--symmetric", "--cipher-algo", cipher_algo, "-o", output_path, input_path]
    try:
        subprocess.run(cmd, check=True)
        # remove original only after success
        os.remove(input_path)
        return output_path
    except FileNotFoundError:
        raise RuntimeError("gpg not found; install gpg to enable encryption")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"gpg failed: {e}")
