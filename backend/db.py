
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "meeting_intelligence")

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
db = client[MONGODB_DB]

if __name__ == "__main__":
    try:
        client.admin.command("ping")
        print("MongoDB Atlas connected successfully!")
        print("Database:", db.name)
    except Exception as e:
        print("MongoDB connection failed:", e)
    finally:
        client.close()
