import os
import requests
import sys

# Configuration
API_URL = "http://localhost:8000/ingest/"
# DEFAULT PDF FOLDER - Change this if your PDFs are elsewhere
PDF_FOLDER = r"c:/Users/joane/OneDrive/Desktop/Sem 8/FastAPI3/PDF/Notifications" 

# If you have multiple folders, you can list them or change the path above
# For now I will point to one of the folders I saw in your file structure earlier

def ingest_pdfs():
    target_folder = PDF_FOLDER
    # Allow overriding via command line arg
    if len(sys.argv) > 1:
        target_folder = sys.argv[1]

    if not os.path.exists(target_folder):
        print(f"Error: Folder '{target_folder}' not found.")
        return

    files = [f for f in os.listdir(target_folder) if f.lower().endswith(".pdf")]
    
    if not files:
        print(f"No PDF files found in '{target_folder}'.")
        return

    print(f"Found {len(files)} PDFs in {target_folder}. Starting ingestion...")

    for filename in files:
        file_path = os.path.join(target_folder, filename)
        
        try:
            with open(file_path, "rb") as f:
                print(f"Ingesting: {filename}...")
                # We send empty tag so the backend infers it
                response = requests.post(
                    API_URL, 
                    files={"file": (filename, f, "application/pdf")},
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
    ingest_pdfs()
