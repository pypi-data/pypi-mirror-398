#!/usr/bin/env python3
# cli.py

import argparse
import sys
import os
import json


from insta_collect.scraper import scrape_hashtag
from insta_collect.saver import save_data

def main():
    parser = argparse.ArgumentParser(description="Instagram hashtag scraper")
    parser.add_argument("--tag", required=True, help="Hashtag target")
    parser.add_argument("--limit", type=int, default=10, help="Jumlah post maksimal")
    parser.add_argument("--cookie", help="Path ke cookies.json", default=None)
    parser.add_argument("--preview", type=int, default=5, help="Preview N post di terminal")
    args = parser.parse_args()

    cookies_path = args.cookie
    if cookies_path and not os.path.exists(cookies_path):
        print(f"[WARNING] File {cookies_path} tidak ditemukan! Menjalankan tanpa login...")
        cookies_path = None

    print(f"[*] Target: #{args.tag} | Limit: {args.limit}")

    # Ambil data dari Instagram
    data = scrape_hashtag(
        hashtag=args.tag,
        limit=args.limit,
        cookies_file=cookies_path
    )

    print(f"[DONE] Mendapatkan {len(data)} data.")

    # Simpan data
    if data:
        filename = f"hasil_{args.tag}.json"
        save_data(data, filename=filename)
        print(f"[INFO] Data tersimpan di {filename}")

if __name__ == "__main__":
    main()
