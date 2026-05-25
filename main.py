from fastapi import FastAPI
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

app = FastAPI(title="Diagnox Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# API Key from environment variable
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

DIVISIONS = ["Dhaka", "Rajshahi", "Chattogram", "Khulna", "Sylhet", "Barishal", "Rangpur", "Mymensingh"]

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

@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        # Create a simple HTML file dynamically
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html>
<head><title>Diagnox Pro</title><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
<h1>🏥 DIAGNOX PRO</h1>
<p>World's Most Advanced AI Medical Platform</p>
<textarea id="symptoms" rows="4" style="width:80%%; padding:10px;" placeholder="Describe your symptoms..."></textarea><br>
<select id="division"><option>Dhaka</option><option>Rajshahi</option><option>Chattogram</option></select><br>
<button onclick="analyze()">Start AI Diagnosis</button>
<div id="result"></div>
<script>
async function analyze(){
    let s=document.getElementById('symptoms').value;
    let l=document.getElementById('division').value;
    let r=document.getElementById('result');
    r.innerHTML='<p>AI analyzing...</p>';
    let res=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symptoms:s,location:l,language:'en'})});
    let d=await res.json();
    if(d.success){
        r.innerHTML='<h3>'+d.response.primary_disease.name+'</h3><p>'+d.response.primary_disease.clinical_reasoning+'</p><p><strong>Severity:</strong> '+d.response.severity+'</p><p><strong>Emergency Risk:</strong> '+d.response.emergency_risk+'</p><p><strong>Medicine:</strong> '+d.response.medicine+'</p>';
        loadDocs(l,d.response.primary_disease.name);
    }
}
async function loadDocs(loc,dis){
    let res=await fetch('/get-doctors',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:loc,disease_name:dis})});
    let d=await res.json();
    let html='<h3>Doctors</h3>';
    d.doctors.forEach(doc=>{html+='<div style="border:1px solid #ccc; margin:10px; padding:10px;"><b>'+doc.name+'</b><br>'+doc.specialty+'<br>'+doc.hospital+'<br>'+doc.address+'<br>Fee: '+doc.fee+'<br>'+doc.contact+'</div>';});
    r.innerHTML+=html;
}
</script>
<p style="margin-top:50px;">⚠️ Consult a doctor for medical advice</p>
</body>
</html>""")
    return FileResponse(index_path)

@app.get("/divisions")
async def get_divisions():
    return {"divisions": DIVISIONS}

@app.post("/analyze")
async def analyze(req: SymptomRequest):
    duration_text = f"{req.duration_value} {req.duration_unit}" if req.duration_value else "Not specified"
    
    prompt = f"""You are an AI doctor. Diagnose based ONLY on these symptoms. NO predefined data.
Symptoms: {req.symptoms}
Age: {req.age if req.age else 'Unknown'}
Duration: {duration_text}
Location: {req.location if req.location else 'Bangladesh'}

Return ONLY JSON:
{{
    "primary_disease": {{"name": "disease name", "confidence_label": "High", "clinical_reasoning": "why this matches"}},
    "severity": "Mild/Moderate/Severe",
    "emergency_risk": "Low/Medium/High",
    "medicine": "medicine advice with disclaimer",
    "doctor_specialty": "specialist type",
    "home_remedy": "home care advice"
}}"""

    ai_response = call_ai(prompt)
    if ai_response:
        parsed = extract_json(ai_response)
        if parsed:
            return {"success": True, "response": parsed}
    
    return {"success": False, "error": "Please provide more details."}

@app.post("/get-doctors")
async def get_doctors(req: dict):
    location = req.get("location", "Dhaka")
    disease_name = req.get("disease_name", "")
    
    prompt = f"""Recommend 4 realistic doctors in {location}, Bangladesh for {disease_name}.
Return ONLY JSON:
{{
    "doctors": [
        {{"name": "Dr. Name", "specialty": "Specialty", "hospital": "Hospital in {location}", "address": "Address", "fee": "fee BDT", "contact": "phone", "available": "time", "experience": "years", "rating": "4.5"}}
    ]
}}"""

    ai_response = call_ai(prompt)
    if ai_response:
        parsed = extract_json(ai_response)
        if parsed and "doctors" in parsed:
            return {"doctors": parsed["doctors"][:4]}
    
    return {"doctors": []}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)