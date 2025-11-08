# backend/app/core/auth.py
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# This will use the Application Default Credentials of the Cloud Run service account
try:
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase Admin SDK initialization error: {e}")
    # In a local environment, you might need to point to a service account JSON file.
    # For Cloud Run, Application Default Credentials should work.

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # tokenUrl is a dummy value

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decodes the Firebase JWT token from the Authorization header and returns user info.
    """
    try:
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        # If the token is invalid for any reason, raise an exception
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )