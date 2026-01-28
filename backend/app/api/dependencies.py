from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.clerk import get_clerk_user_id
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Verifies the Clerk JWT token and returns the User model.
    """
    token = credentials.credentials
    clerk_user_id = get_clerk_user_id(token)
    
    # Get or create user in database
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user:
        # User doesn't exist in our DB yet - create them
        # In production, you might want to sync with Clerk webhooks
        # For now, we'll create a basic user record
        user = User(
            clerk_user_id=clerk_user_id,
            name="",  # Will be updated from Clerk user data
            current_applying_role=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user
