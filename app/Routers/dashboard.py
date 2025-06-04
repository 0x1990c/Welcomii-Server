import secrets
import os
import time
import requests
import app.Utils.database_handler as crud
import app.Utils.Auth as Auth

from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import AsyncSessionLocal
from app.Utils.Auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from app.Utils.sendgrid import send_mail, send_approve_email, forgot_password_func
from app.Model.AuthModel import SignInModel, SignUpModel
from typing import Annotated
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
router = APIRouter()

from selenium import webdriver
from bs4 import BeautifulSoup
import time

openai_api_key = os.getenv('OPENAI_API_KEY')

# Dependency to get the database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/getInfoAirbnbList")
async def getInfoAirbnbList(airbnbUrl: str = Form(...), wifiCode: str = Form(...), listingTitle: str = Form(...), hostName: str = Form(...), db: Session = Depends(get_db)):
    
    try:
        url = airbnbUrl

        results = {}
         
        driver = webdriver.Chrome()
        driver.get(url)
        time.sleep(15)  # Give it time to render JavaScript

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        title_div = soup.find("div", class_="_1e9g34tc")
        h1_tag = title_div.find("h1", class_="hpipapi")
        results['Title'] = h1_tag.get_text(strip=True)

        location_div = soup.find("div", class_="t1kjrihn")
        h2_tag = location_div.find("h2", class_="hpipapi")
        results['Location'] = h2_tag.get_text(strip=True)

        description_div = soup.find("div", class_="d1isfkwk")
        span_tag = description_div.find("span", class_="l1h825yc")
        results['Description'] = span_tag.get_text(strip=True)

        host_div = soup.find("div", class_="t1lpv951")
        results['Host'] = host_div.get_text(strip=True)
        
        print(results);
    
        # driver.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
