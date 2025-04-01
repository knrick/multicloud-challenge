from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os

security = HTTPBasic()

def get_admin_credentials():
    """Get admin credentials from environment variables"""
    return {
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "changeme")  # Default password, should be changed in production
    }

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    admin_credentials = get_admin_credentials()
    correct_username = secrets.compare_digest(credentials.username, admin_credentials["username"])
    correct_password = secrets.compare_digest(credentials.password, admin_credentials["password"])
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username 