import os
import requests
import sys

# Configuration
API_URL = "http://localhost:8000/ingest/"
# Default to the data directory in the current project
DEFAULT_FOLDER = os.path.join(os.getcwd(), "data")

def ingest_documents():
    target_folder = DEFAULT_FOLDER
    # Allow overriding via command line arg
    if len(sys.argv) > 1:
        target_folder = sys.argv[1]

    if not os.path.exists(target_folder):
        print(f"Error: Folder '{target_folder}' not found.")
        return

    print(f"Scanning for documents in '{target_folder}'...")

    supported_extensions = ('.pdf', '.md')
    files_to_ingest = []

    # Recursive search
    for root, dirs, files in os.walk(target_folder):
        for file in files:
            if file.lower().endswith(supported_extensions):
                files_to_ingest.append(os.path.join(root, file))
    
    if not files_to_ingest:
        print(f"No supported files {supported_extensions} found in '{target_folder}'.")
        return

    print(f"Found {len(files_to_ingest)} documents. Starting ingestion...")

    for file_path in files_to_ingest:
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, "rb") as f:
                print(f"Ingesting: {filename}...")
                
                # Determine content type (optional, requests handles it usually but good to be explicit if needed)
                content_type = "application/pdf" if filename.lower().endswith(".pdf") else "text/markdown"
                
                # We send empty tag so the backend infers it or leaves it null
                response = requests.post(
                    API_URL, 
                    files={"file": (filename, f, content_type)},
                    data={"tag": ""} 
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success: {filename} | Tag: {data.get('tag', 'N/A')} | Chunks: {data.get('chunks_count', 'N/A')}")
                else:
                    print(f"❌ Failed: {filename} - {response.text}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

if __name__ == "__main__":
    ingest_documents()
