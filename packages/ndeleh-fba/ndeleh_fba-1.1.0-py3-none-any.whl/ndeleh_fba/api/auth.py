# src/ndeleh_fba/api/auth.py

from fastapi import Header, HTTPException, status
import os


API_KEY = "gm-secret-key-2025"   # <-- You can change this later

async def get_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")
    return True
