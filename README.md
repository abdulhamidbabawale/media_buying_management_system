# Media Buying Management System

A centralized API-only system built with **FastAPI** to manage advertising campaigns across multiple platforms (Google, Meta, TikTok, LinkedIn, etc.) with multi-tenant support and intelligence-driven optimization.

## Features
- Multi-tenant API architecture  
- Global rate limiting using **Redis**  
- Authentication with **JWT**  
- MongoDB integration for data storage  
- Modular endpoints for clients and authentication  
- Healthcheck endpoint  

## Tech Stack
- **Backend:** FastAPI, Python (async)  
- **Database:** MongoDB  
- **Caching / Rate Limiting:** Redis  
- **Authentication:** JWT  
- **Testing:** pytest, pytest-asyncio  
- **HTTP Client for Tests:** httpx  

## Installation
```bash
git clone <repo_url>
cd media_buying_management_system
python -m venv env
source env/bin/activate  # On Linux/Mac
# .\env\Scripts\activate  # On Windows
pip install -r requirements.txt
```

## Running the App
```bash
uvicorn app.main:app --reload
```
