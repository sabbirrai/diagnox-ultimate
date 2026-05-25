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

# ALL 64 DISTRICTS (JELA) OF BANGLADESH
DISTRICTS = [
    "Dhaka", "Faridpur", "Gazipur", "Gopalganj", "Kishoreganj", "Madaripur", "Manikganj", "Munshiganj",
    "Narayanganj", "Narsingdi", "Rajbari", "Shariatpur", "Tangail", "Bandarban", "Brahmanbaria", "Chandpur",
    "Chattogram", "Cox's Bazar", "Comilla", "Feni", "Khagrachari", "Lakshmipur", "Noakhali", "Rangamati",
    "Habiganj", "Moulvibazar", "Sunamganj", "Sylhet", "Bagerhat", "Chuadanga", "Jessore", "Jhenaidah",
    "Khulna", "Kushtia", "Magura", "Meherpur", "Narail", "Satkhira", "Barguna", "Barishal", "Bhola",
    "Jhalokathi", "Patuakhali", "Pirojpur", "Bogra", "Joypurhat", "Naogaon", "Natore", "Chapai Nawabganj",
    "Pabna", "Rajshahi", "Sirajganj", "Dinajpur", "Gaibandha", "Kurigram", "Lalmonirhat", "Nilphamari",
    "Panchagarh", "Rangpur", "Thakurgaon", "Jamalpur", "Mymensingh", "Netrokona", "Sherpur"
]

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
        # Create HTML with all districts
        district_options = "\n".join([f'<option value="{d}">{d}</option>' for d in DISTRICTS])
        html_content = f"""<!DOCTYPE html>
<html>
<head><title>Diagnox Pro</title><meta charset="UTF-8"></head>
<body style="font-family: sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
<div style="max-width: 800px; margin: 0 auto; background: white; border-radius: 20px; padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
<h1 style="color: #667eea;">🏥 DIAGNOX PRO</h1>
<p>World's Most Advanced AI Medical Platform</p>
<p style="color: #666;">Any Disease | Any District | Free Forever</p>
<textarea id="symptoms" rows="4" style="width:100%; padding:10px; border:1px solid #ddd; border-radius:10px;" placeholder="Describe your symptoms...&#10;Example: fever, headache, body pain for 3 days"></textarea><br>
<select id="district" style="width:100%; padding:10px; margin:10px 0; border:1px solid #ddd; border-radius:10px;">
<option value="">Select Your District</option>
{district_options}
</select><br>
<button onclick="analyze()" style="width:100%; padding:15px; background: linear-gradient(135deg, #667eea, #764ba2); color:white; border:none; border-radius:10px; font-size:18px; cursor:pointer;">🔍 Start AI Diagnosis</button>
<div id="result" style="margin-top:20px;"></div>
<p style="margin-top:30px; font-size:12px; color:#999;">⚠️ This AI analysis is for informational purposes only. Always consult a licensed physician.</p>
</div>
<script>
async function analyze(){{
    let s=document.getElementById('symptoms').value;
    let d=document.getElementById('district').value;
    if(!s){{ alert('Please describe your symptoms!'); return; }}
    if(!d){{ alert('Please select your district!'); return; }}
    let r=document.getElementById('result');
    r.innerHTML='<div style="text-align:center"><div style="border:4px solid #f3f3f3; border-top:4px solid #667eea; border-radius:50%; width:40px; height:40px; animation:spin 1s linear infinite; margin:0 auto;"></div><p>AI is analyzing your symptoms...</p></div><style>@keyframes spin{{0%{{transform:rotate(0deg)}}100%{{transform:rotate(360deg)}}}}</style>';
    try{{
        let res=await fetch('/analyze',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{symptoms:s,location:d,language:'en'}})}});
        let data=await res.json();
        if(data.success){{
            let resp=data.response;
            r.innerHTML='<div style="background:#f0f0f0; padding:20px; border-radius:10px; text-align:left;">'+
                '<h3 style="color:#667eea;">🩺 '+resp.primary_disease.name+'</h3>'+
                '<p><strong>🧠 Reasoning:</strong> '+resp.primary_disease.clinical_reasoning+'</p>'+
                '<p><strong>📊 Severity:</strong> '+resp.severity+'</p>'+
                '<p><strong>🚨 Emergency Risk:</strong> '+resp.emergency_risk+'</p>'+
                '<p><strong>💊 Medicine:</strong> '+resp.medicine+'</p>'+
                '<p><strong>🏠 Home Care:</strong> '+resp.home_remedy+'</p>'+
                '<p><strong>👨‍⚕️ Recommended Specialist:</strong> '+resp.doctor_specialty+'</p>'+
                '</div>';
            loadDoctors(d,resp.primary_disease.name);
        }}else{{
            r.innerHTML='<p style="color:red;">Unable to analyze. Please provide more details.</p>';
        }}
    }}catch(e){{
        r.innerHTML='<p style="color:red;">Error: '+e.message+'</p>';
    }}
}}
async function loadDoctors(district,disease){{
    let r=document.getElementById('result');
    try{{
        let res=await fetch('/get-doctors',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{location:district,disease_name:disease}})}});
        let data=await res.json();
        if(data.doctors && data.doctors.length){{
            let html='<div style="margin-top:20px;"><h3>👨‍⚕️ Recommended Doctors in '+district+'</h3>';
            data.doctors.forEach(doc=>{{
                html+='<div style="background:#f9f9f9; padding:15px; margin:10px 0; border-radius:10px; border-left:4px solid #667eea;">'+
                    '<strong>👨‍⚕️ '+doc.name+'</strong><br>'+
                    '🩺 '+doc.specialty+'<br>'+
                    '🏥 '+doc.hospital+'<br>'+
                    '📍 '+doc.address+'<br>'+
                    '💰 Fee: '+doc.fee+'<br>'+
                    '📞 '+doc.contact+'<br>'+
                    '⏰ '+doc.available+'<br>'+
                    '⭐ '+doc.rating+' ('+doc.experience+')'+
                    '</div>';
            }});
            html+='</div>';
            r.innerHTML+=html;
        }}
    }}catch(e){{ console.log(e); }}
}}
</script>
</body>
</html>"""
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    return FileResponse(index_path)

@app.get("/districts")
async def get_districts():
    return {"districts": DISTRICTS}

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
        {{"name": "Dr. Name", "specialty": "Specialty", "hospital": "Hospital in {location}", "address": "Address in {location}", "fee": "fee BDT", "contact": "phone", "available": "time", "experience": "years", "rating": "4.5"}}
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