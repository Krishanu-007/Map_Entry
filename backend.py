from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

# Allow CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to specific domains for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Retrieve MongoDB URI from environment variable
mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    raise ValueError("MONGO_URI environment variable is not set")

# Initialize MongoDB client
client = AsyncIOMotorClient(mongo_uri)

db = client.Backend_Test  
collection = db.Trial_Test2

# Data model for location
class locData(BaseModel):
    common_id: str
    latitude: float
    longitude: float

# API endpoint to post location data
@app.post("/testPost")
async def send_data(data: locData):
    if data.latitude == 0.0 or data.longitude == 0.0:
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    geoJsonData = {
        "common_id": data.common_id,
        "type": "Point",
        "coordinates": [data.latitude, data.longitude],
        "timestamp": datetime.utcnow()  # Add the current UTC timestamp
    }

    try:
        result = await collection.insert_one(geoJsonData)
        return {"message": "Data saved", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")

# API endpoint to fetch location data by common_id
@app.get("/fetchData/{common_id}")
async def fetch_data(common_id: str):
    try:
        cursor = collection.find({"common_id": common_id}).sort("timestamp", 1)

        data_list = []
        async for data in cursor:
            data_list.append(data["coordinates"])

        if not data_list:
            raise HTTPException(status_code=404, detail="No data found for this common_id")

        return {
            "common_id": common_id,
            "path": data_list  # Return a list of coordinates as a path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

# Serve the frontend HTML file
@app.get("/")
def serve_frontend():
    return FileResponse("index.html")
