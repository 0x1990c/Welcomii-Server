from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import AsyncSessionLocal
import app.Utils.database_handler as crud
import os
from dotenv import load_dotenv
from typing import Annotated

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

# Dependency to get the database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def authenticate_user(db: Session, email: str, password: str):
    user = await crud.get_user_by_email_approved(db, email)  # This function should be defined in your crud.py
    # print("authenticater_user: ", user.password)

    print("sigin user: ", user);
    if user is None:
        return 3 # error fetch user data
    elif user is False:
        return 2 # non approved
    
    if not verify_password(password, user.password):  # Assuming 'hashed_password' is an attribute of the User model
        return 1 # password is not correct

    return user  # all is success

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=1000)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    # return "isachenkoanton28@gmail.com"
    print("token: ", token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name = payload.get("sub")
        # print("decode user_name: ", user_name)
        if user_name is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # user = await crud.get_user_by_email(db, email)  # This function should be defined in your crud.py
    # print("user: ", user)
    # if user is None:
    #     raise credentials_exception
    # return user
    return user_name
