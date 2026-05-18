from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "pegy_calculator")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
pegy_collection = db["pegy_records"]

async def init_db():
    try:
        await pegy_collection.create_index("symbol")
        await pegy_collection.create_index([("pegy_ratio", 1)])
        print("✅ PEGY Database connected!")
    except Exception as e:
        print(f"⚠️ Index warning: {e}")
