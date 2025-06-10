import secrets
import os
import time
import requests
import openai
import json
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

openai.api_key = os.getenv('OPENAI_API_KEY')

DEFAULT_GUIDE = {
    "welcome_message": "Welcome to our home! We hope you enjoy your stay.",
    "house_rules": "No smoking. No pets. Quiet hours after 10 PM.",
    "local_recommendations": "Try the local cafe on Main Street, and visit the downtown farmers market.",
    "checkout_instructions": "Please check out by 11 AM and leave the key in the lockbox."
}

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
        
        images = []
        image_tags = soup.find_all("img")

        for img in image_tags:
            src = img.get("src")
            if src and "jpg" in src:
                images.append(src)

        results["Images"] = images

        print(results);
    
        guide = generate_guide_with_fallback(
            title=results['Title'],
            description=results['Description'],
            location=results['Location'],
            custom_info=results['Host'],
            images=results["Images"]
        )
        
        return json.dumps(guide, indent=2)
        # driver.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def build_airbnb_prompt(title, description, location, custom_info):
    return (
        f"You are an assistant that returns ONLY valid JSON. "
        f"Do not include any explanation or text outside the JSON.\n\n"
        f"Generate a JSON guide with the following fields:\n"
        f"- welcome_message\n"
        f"- house_rules\n"
        f"- local_recommendations\n"
        f"- checkout_instructions\n\n"
        f"Title: {title}\n"
        f"Description: {description}\n"
        f"Location: {location}\n"
        f"Custom Info: {custom_info}"
    )

async def generate_guide_with_fallback(title, description, location, custom_info, images):
    try:
        # Use the Chat API with gpt-3.5-turbo
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that only returns valid JSON without explanation."},
                {"role": "user", "content": build_airbnb_prompt(title, description, location, custom_info)},
            ],
            temperature=0.7
        )

        raw_text = response.choices[0].message["content"].strip()

        # Try to parse JSON (you can optionally extract the JSON block if needed)
        parsed = json.loads(raw_text)

        # Merge with defaults
        guide = {
            "welcome_message": parsed.get("welcome_message", DEFAULT_GUIDE["welcome_message"]),
            "house_rules": parsed.get("house_rules", DEFAULT_GUIDE["house_rules"]),
            "local_recommendations": parsed.get("local_recommendations", DEFAULT_GUIDE["local_recommendations"]),
            "checkout_instructions": parsed.get("checkout_instructions", DEFAULT_GUIDE["checkout_instructions"]),
        }
        return guide

    except Exception as e:
        print("❌ Failed to generate guide. Error:", str(e))
        return DEFAULT_GUIDE