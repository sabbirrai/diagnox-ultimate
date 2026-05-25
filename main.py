from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import os
import uvicorn
import json
import random
from typing import Optional
from datetime import datetime

app = FastAPI(title="Diagnox Pro", description="World's Most Advanced AI Medical Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# API Key from environment variable - NO HARDCODED KEY
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

DIVISIONS = ["Dhaka", "Rajshahi", "Chattogram", "Khulna", "Sylhet", "Barishal", "Rangpur", "Mymensingh", 
             "Cox's Bazar", "Comilla", "Narayanganj", "Gazipur", "Tangail", "Jessore", "Bogra", "Dinajpur",
             "Pabna", "Noakhali", "Feni", "Kushtia", "Satkhira"]

class SymptomRequest(BaseModel):
    symptoms: str
    age: Optional[int] = None
    gender: Optional[str] = None
    duration_value: Optional[int] = None
    duration_unit: Optional[str] = None
    location: Optional[str] = None
    blood_group: Optional[str] = None
    language: str = "en"

def call_ai(prompt):
    if not OPENROUTER_API_KEY:
        return None
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 4000
            },
            timeout=90
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"AI Error: {e}")
    return None

def extract_json(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            return json.loads(text[start:end])
    except:
        pass
    return None

@app.post("/analyze")
async def analyze(req: SymptomRequest):
    duration_text = f"{req.duration_value} {req.duration_unit}" if req.duration_value else "Not specified"
    
    if req.language == "bn":
        lang_text = """তুমি একজন বিশ্বমানের AI ডাক্তার। তুমি পৃথিবীর যেকোনো রোগ নির্ণয় করতে পারো।
শুধুমাত্র বাংলা ভাষায় উত্তর দাও। কোনো প্রি-ডিফাইন্ড ডাটা ব্যবহার করবে না।
শুধু রোগীর বর্ণিত উপসর্গের ভিত্তিতে বাস্তবসম্মত বিশ্লেষণ দাও।"""
    else:
        lang_text = """You are a world-class AI doctor. You can diagnose ANY disease in the world.
Do NOT use any predefined data. Analyze based ONLY on patient's described symptoms.
Give professional, realistic medical analysis."""
    
    prompt = f"""{lang_text}

PATIENT:
- Symptoms: {req.symptoms}
- Age: {req.age if req.age else 'Not specified'}
- Gender: {req.gender if req.gender else 'Not specified'}
- Duration: {duration_text}
- Location: {req.location if req.location else 'Bangladesh'}

Provide diagnosis in EXACT JSON format:

{{
    "primary_disease": {{
        "name": "disease name",
        "confidence_label": "High/Moderate/Low",
        "confidence_score": 85,
        "match_score": 8,
        "clinical_reasoning": "detailed medical reasoning"
    }},
    "alternative_diseases": [
        {{"name": "alternative 1", "confidence_label": "Moderate", "confidence_score": 65}},
        {{"name": "alternative 2", "confidence_label": "Low", "confidence_score": 45}}
    ],
    "severity": "Mild/Moderate/Severe",
    "severity_description": "description",
    "severity_percentage": 65,
    "emergency_risk": "Low/Medium/High",
    "matched_symptoms": ["symptom1", "symptom2"],
    "missing_symptoms": ["symptom1", "symptom2"],
    "action_items": ["action1", "action2", "action3"],
    "medicine": "medicine advice with disclaimer",
    "doctor_specialty": "specialist type",
    "emergency_warning": "critical warning signs",
    "home_remedy": "home care",
    "recommended_tests": ["test1", "test2"],
    "simple_explanation": "easy explanation",
    "follow_up_questions": ["question1", "question2"],
    "precautions": ["precaution1", "precaution2"],
    "diet": "diet advice",
    "recovery_time": "expected recovery"
}}"""

    ai_response = call_ai(prompt)
    if ai_response:
        parsed = extract_json(ai_response)
        if parsed:
            severity_pct = parsed.get("severity_percentage", 50)
            health_score = max(30, min(100, 100 - int(severity_pct)))
            parsed["health_score"] = health_score
            return {"success": True, "response": parsed}
    
    return {"success": False, "error": "Please provide more detailed symptoms."}

@app.post("/get-doctors")
async def get_doctors(req: dict):
    location = req.get("location", "Dhaka")
    disease_name = req.get("disease_name", "")
    doctor_specialty = req.get("doctor_specialty", "General Physician")
    language = req.get("language", "en")
    
    if language == "bn":
        lang_text = f"{location}, বাংলাদেশের {disease_name} রোগের জন্য ৪ জন ডাক্তারের তথ্য দাও। বাস্তবসম্মত তথ্য দাও।"
    else:
        lang_text = f"Recommend 4 doctors in {location}, Bangladesh for {disease_name}. Give realistic information."
    
    prompt = f"""{lang_text}

Return JSON:
{{
    "doctors": [
        {{
            "name": "Dr. Name",
            "specialty": "{doctor_specialty}",
            "hospital": "Hospital in {location}",
            "address": "Address in {location}",
            "fee": "fee BDT",
            "contact": "phone",
            "available": "days time",
            "experience": "years",
            "rating": "4.5",
            "qualification": "MBBS"
        }}
    ]
}}"""

    ai_response = call_ai(prompt)
    if ai_response:
        parsed = extract_json(ai_response)
        if parsed and "doctors" in parsed:
            return {"doctors": parsed["doctors"][:4]}
    
    return {"doctors": []}

@app.get("/divisions")
async def get_divisions():
    return {"divisions": DIVISIONS}

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)