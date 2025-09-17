from fastapi import HTTPException, Request, status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def role_required(allowed_roles):
    def dependency(request: Request):
        role_id = request.session.get("role_id")
        if not role_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        if role_id not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
    return Depends(dependency)

async def current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user