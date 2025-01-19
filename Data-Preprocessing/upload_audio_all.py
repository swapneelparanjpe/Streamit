import requests
from pymongo import MongoClient
from bson.binary import Binary
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# MongoDB configuration
MONGO_URI = "mongodb+srv://streamify-admin:" + os.environ.get('STREAMIFY_USER_PASSWORD') + "@streamify-cluster.nf1vv.mongodb.net/"
DB_NAME = "streamify-db"
COLLECTION_NAME = "songs"

# Path to the CSV file
csv_file_path = "./music_dataset.csv"

# Required attributes
required_fields = [
    "artistName",
    "country",
    "previewUrl",
    "genreName",
    "releaseDate",
    "trackName",
    "albumName",
    "duration",
    "coverImage"
]

# Convert duration from milliseconds to seconds
def convert_duration_to_seconds(duration_ms):
    try:
        return int(duration_ms) // 1000  # Convert ms to seconds
    except ValueError:
        return None

# Function to process a single row
def process_row(row, collection):
    # Extract only required fields
    document = {field: row[field] for field in required_fields if field in row}

    # Convert duration to seconds
    if "duration" in document and document["duration"]:
        document["duration"] = convert_duration_to_seconds(document["duration"])

    # Fetch audio data from previewUrl
    if "previewUrl" in document and document["previewUrl"]:
        try:
            response = requests.get(document["previewUrl"])
            if response.status_code == 200:
                document["audioData"] = Binary(response.content)
            else:
                print(f"Failed to download audio for {document.get('trackName', 'Unknown')}: {response.status_code}")
                document["audioData"] = None
        except requests.RequestException as e:
            print(f"Request failed for {document.get('trackName', 'Unknown')}: {e}")
            document["audioData"] = None

    # Insert the document into the database
    try:
        collection.insert_one(document)
        return True  # Successful upload
    except Exception as e:
        print(f"Failed to upload document: {e}")
        return False  # Failed upload

if __name__ == "__main__":
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Track upload counts
    total_records = 0
    successfully_uploaded = 0

    # Open the CSV file and read records
    with open(csv_file_path, encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        rows_to_process = list(csv_reader)[:500]

        # Use ThreadPoolExecutor for multithreading
        with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust the number of threads as needed
            future_to_row = {executor.submit(process_row, row, collection): row for row in rows_to_process}

            for future in as_completed(future_to_row):
                total_records += 1
                if future.result():  # Check if the upload was successful
                    successfully_uploaded += 1
                    print(f"{successfully_uploaded} songs uploaded successfully")

    # Print upload summary
    print(f"Upload complete. Total Records Processed: {total_records}")
    print(f"Successfully Uploaded: {successfully_uploaded}")
    print(f"Failed Uploads: {total_records - successfully_uploaded}")
