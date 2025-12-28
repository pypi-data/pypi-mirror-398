import json
import csv

def save_data(data, filename="results"):
    json_path = f"{filename}.json"
    csv_path = f"{filename}.csv"


    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


    keys = data[0].keys()
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    print(f"[✓] Saved to {json_path} & {csv_path}")

