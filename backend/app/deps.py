from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .security import decode_token
oauth=OAuth2PasswordBearer(tokenUrl='/api/auth/login')
def current_user(token:str=Depends(oauth),db:Session=Depends(get_db)):
 payload=decode_token(token);uid=payload.get('sub') if payload else None;u=db.get(User,int(uid)) if uid and str(uid).isdigit() else None
 if not u or not u.is_active or int(payload.get('ver',0))!=int(u.token_version or 0): raise HTTPException(401,'Authentication required')
 return u
def admin_user(u:User=Depends(current_user)):
 if not u.is_admin: raise HTTPException(403,'Admin access required')
 return u
