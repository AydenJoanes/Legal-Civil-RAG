import os
import requests
import sys

# Configuration
API_URL = "http://localhost:8000/ingest/"

# Markdown folders to ingest
MD_FOLDERS = [
    r"c:/Users/joane/OneDrive/Desktop/Sem 8/FastAPI3/MD/circularMD",
    r"c:/Users/joane/OneDrive/Desktop/Sem 8/FastAPI3/MD/notificationsMD",
]


def ingest_markdown():
    # Allow overriding via command line arg (single folder)
    if len(sys.argv) > 1:
        folders = [sys.argv[1]]
    else:
        folders = MD_FOLDERS

    total_success = 0
    total_failed = 0

    for folder in folders:
        if not os.path.exists(folder):
            print(f"⚠️  Folder not found, skipping: {folder}")
            continue

        files = [f for f in os.listdir(folder) if f.lower().endswith(".md")]

        if not files:
            print(f"No .md files found in '{folder}'.")
            continue

        folder_name = os.path.basename(folder)
        print(f"\n{'='*60}")
        print(f"📂 Folder: {folder_name} ({len(files)} markdown files)")
        print(f"{'='*60}")

        for filename in files:
            file_path = os.path.join(folder, filename)

            try:
                with open(file_path, "rb") as f:
                    print(f"  Ingesting: {filename}...", end=" ")
                    response = requests.post(
                        API_URL,
                        files={"file": (filename, f, "text/markdown")},
                        data={"tag": ""}  # Let backend infer the tag
                    )

                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Tag: {data.get('tag', 'N/A')} | Chunks: {data.get('chunks_stored', 'N/A')}")
                        total_success += 1
                    else:
                        print(f"❌ {response.status_code} - {response.text}")
                        total_failed += 1
            except Exception as e:
                print(f"❌ Error: {e}")
                total_failed += 1

    print(f"\n{'='*60}")
    print(f"📊 Done! Success: {total_success} | Failed: {total_failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    ingest_markdown()
