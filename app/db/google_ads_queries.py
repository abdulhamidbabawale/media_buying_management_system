from fastapi import HTTPException
from app.db.connection import db

# Setup Mongo client once (probably in db.py)
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
    required_fields = ["developer_token", "client_id", "client_secret", "refresh_token"]
    missing = [f for f in required_fields if f not in google_ads_config]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required Google Ads fields: {', '.join(missing)}"
        )

    return {
        "developer_token": google_ads_config["developer_token"],
        "client_id": google_ads_config["client_id"],
        "client_secret": google_ads_config["client_secret"],
        "refresh_token": google_ads_config["refresh_token"],
        "login_customer_id": google_ads_config.get("login_customer_id"),
    }


def save_campaign_to_db(campaign_obj: dict):
    campaigns_collection.insert_one(campaign_obj.dict())

