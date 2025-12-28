#!/usr/bin/env python3
import argparse
import json
from html_parser import parse_instagram_html
from exporter import save_to_xlsx


def main():
    parser = argparse.ArgumentParser(description="Instagram HTML Comment Extractor")
    parser.add_argument("html_file", help="Path to Instagram HTML file")
    parser.add_argument(
        "--preview",
        type=int,
        default=0,
        help="Show N comments as preview in terminal"
    )

    args = parser.parse_args()

    # 1. Parse HTML
    data = parse_instagram_html(args.html_file)

    # 2. Save JSON (default behavior)
    json_output = "instagram_comments.json"
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 3. Save XLSX (AUTOMATIC)
    xlsx_output = save_to_xlsx(data)

    print(f"[+] Total entries saved: {len(data)}")
    print(f"[+] JSON output: {json_output}")
    print(f"[+] XLSX output: {xlsx_output}")

    # 4. Preview (optional)
    if args.preview > 0:
        print("\n--- PREVIEW ---")
        for i, d in enumerate(data[:args.preview], 1):
            print(f"{i}. @{d['username']}: {d['text'][:100]}")


if __name__ == "__main__":
    main()
