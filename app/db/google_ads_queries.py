from fastapi import HTTPException
from app.db.connection import db
from fastapi.encoders import jsonable_encoder

collection =  db.google_ads_connection
campaigns_collection=db.google_ads_campaign

async def get_user_config(user_id: str) -> dict:
    """
    Fetch the stored Google Ads config for a given user.
    """
    user = await collection.find_one({"_id": user_id})

    if not user or "google_ads" not in user:
        raise HTTPException(status_code=404, detail="Google Ads config not found for user")

    google_ads_config = user["google_ads"]

    # Validate that required fields exist
    required_fields = ["customer_id", "refresh_token"]
    missing = [f for f in required_fields if f not in google_ads_config]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required Google Ads fields: {', '.join(missing)}"
        )

    return {
        "customer_id": google_ads_config["customer_id"],
        "refresh_token": google_ads_config["refresh_token"],
    }


async def save_campaign_to_db(campaign_obj: dict):
    campaign_dict = jsonable_encoder(campaign_obj)
    result=await campaigns_collection.insert_one(campaign_dict)
    return str(result.inserted_id)


async def get_campaigns_for_user( user_id: str):
    query = {"client_id": user_id} if user_id else {}
    return await campaigns_collection.find(query).to_list(100)

async def get_campaign_by_id(campaign_id: str, client_id: str):
    return await campaigns_collection.find_one(
        {"_id": campaign_id, "client_id": client_id}
    )
    
async def update_campaign_status_in_db(campaign_id: str, new_status: str):
    """Update campaign status in MongoDB."""
    result = await campaigns_collection.update_one(
        {"_id": campaign_id},
        {"$set": {"status": new_status.upper()}}
    )
    return result.modified_count > 0    