from pymongo import MongoClient
import os

MONGO_URI = "mongodb+srv://streamify-admin:" + os.environ.get('STREAMIFY_USER_PASSWORD') + "@streamify-cluster.nf1vv.mongodb.net/"
DB_NAME = "streamify-db"
COLLECTION_NAME = "songs"

def connect_mongodb():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    return collection


def upload_audio_file(request):

    document = {
        "audioData" : request.FILES["audioData"].read(),
        "coverImage" : request.FILES["coverImage"].read(),
        "trackName" : request.POST["trackName"],
        "artistName" : request.POST["artistName"],
        "genreName" : request.POST["genreName"],
        "albumName" : request.POST["albumName"],
        "country" : request.POST["country"],
        "releaseDate" : request.POST["releaseDate"],
    }
    
    collection = connect_mongodb()
    result = collection.insert_one(document)
    print(f"Track uploaded successfully. Document ID: {result.inserted_id}")


def get_search_results(search_text):
    collection = connect_mongodb()

    query = {
    "$or": [
        {"artistName": {"$regex": search_text, "$options": "i"}},
        {"genreName": {"$regex": search_text, "$options": "i"}},
        {"trackName": {"$regex": search_text, "$options": "i"}}
    ]
}
    results = list(collection.find(query).limit(18))

    return results
