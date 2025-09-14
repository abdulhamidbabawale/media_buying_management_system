# from pymongo import MongoClient

# client = MongoClient("mongodb+srv://hamidbabawale_db_user:ZMSHm4o2DdDOBIbm@cluster0.hw6mbn9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# client = None
# db = None

client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client['hamidbabawale_db_user']
