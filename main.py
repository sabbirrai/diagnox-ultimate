from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import os
import uvicorn
import json
from typing import Optional

app = FastAPI(title="Diagnox Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# ALL 64 DISTRICTS OF BANGLADESH
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

district_options_html = ""
for d in DISTRICTS:
    district_options_html += f'<option value="{d}">{d}</option>'

HTML_PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnox Pro - AI Medical Platform</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #667eea; text-align: center; margin-bottom: 30px; }}
        h3 {{ color: #667eea; margin-bottom: 20px; }}
        textarea, input, select {{
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 10px;
            font-size: 14px;
        }}
        button {{
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            cursor: pointer;
            margin-top: 10px;
        }}
        button:hover {{ opacity: 0.9; transform: translateY(-2px); }}
        .result {{ margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px; display: none; }}
        .loading {{ text-align: center; padding: 20px; display: none; }}
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        .doctor-card {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .row {{ display: flex; gap: 15px; flex-wrap: wrap; }}
        .row > div {{ flex: 1; }}
        .gender-group {{ display: flex; gap: 20px; margin: 10px 0; }}
        .gender-group label {{ display: flex; align-items: center; gap: 5px; }}
        @media (max-width: 768px) {{ .card {{ padding: 20px; }} .row {{ flex-direction: column; }} }}
        .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🏥 DIAGNOX PRO</h1>
            <h3 style="text-align:center;">World's Most Advanced AI Medical Platform</h3>
            <p style="text-align:center; color:#666;">Any Disease | Any District | Free Forever</p>
        </div>

        <div class="card">
            <h3>🩺 AI Clinical Intelligence - Any Disease Worldwide</h3>
            <textarea id="symptoms" rows="4" placeholder="Describe your symptoms in detail...&#10;Example: I have fever, headache, body pain for 3 days"></textarea>
            
            <div class="row">
                <div><input type="number" id="age" placeholder="Age"></div>
                <div><div style="display:flex; gap:10px;"><input type="number" id="durationValue" placeholder="Duration" style="flex:2"><select id="durationUnit" style="flex:1"><option value="days">Days</option><option value="weeks">Weeks</option><option value="months">Months</option></select></div></div>
            </div>
            
            <div class="gender-group">
                <label><input type="radio" name="gender" value="Male"> Male</label>
                <label><input type="radio" name="gender" value="Female"> Female</label>
                <label><input type="radio" name="gender" value="Other"> Other</label>
            </div>
            
            <select id="districtSelect" style="width:100%; padding:12px; border:1px solid #ddd; border-radius:10px;">
                <option value="">-- Select Your District (64 Districts) --</option>
                {district_options_html}
            </select>
            
            <button onclick="analyze()">🔍 Start AI Diagnosis</button>
            
            <div class="loading" id="loading"><div class="spinner"></div><p>🧠 AI is analyzing your symptoms...</p></div>
            <div class="result" id="result"></div>
            
            <div class="legal-disclaimer" style="margin-top:20px; padding:15px; background:#f0f0f0; border-radius:10px; font-size:12px; text-align:center;">
                ⚕️ This AI analysis is for informational purposes only. Always consult a licensed physician.
            </div>
        </div>

        <div class="footer">
            <p>© 2024 Diagnox Pro | Any Disease | Any District | 24/7 Available</p>
        </div>
    </div>

    <script>
        async function analyze() {{
            const symptoms = document.getElementById('symptoms').value.trim();
            if (!symptoms) {{
                alert('Please describe your symptoms!');
                return;
            }}
            const location = document.getElementById('districtSelect').value;
            if (!location) {{
                alert('Please select your district!');
                return;
            }}
            const age = document.getElementById('age').value;
            const gender = document.querySelector('input[name="gender"]:checked')?.value || '';
            const durationValue = document.getElementById('durationValue').value;
            const durationUnit = document.getElementById('durationUnit').value;
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {{
                const response = await fetch('/analyze', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        symptoms: symptoms,
                        age: age ? parseInt(age) : null,
                        gender: gender,
                        duration_value: durationValue ? parseInt(durationValue) : null,
                        duration_unit: durationUnit,
                        location: location,
                        language: 'en'
                    }})
                }});
                const data = await response.json();
                document.getElementById('loading').style.display = 'none';
                if (data.success && data.response) {{
                    const d = data.response;
                    let html = `
                        <h3 style="color:#667eea;">🩺 ${{d.primary_disease?.name || 'Analysis Complete'}}</h3>
                        <div style="background:#e8e8ff; padding:15px; border-radius:10px; margin:10px 0;">
                            <strong>🧠 Clinical Reasoning:</strong><br>${{d.primary_disease?.clinical_reasoning || 'Analysis based on your symptoms'}}
                        </div>
                        <div class="row" style="margin:15px 0;">
                            <div style="background:#f0f0f0; padding:15px; border-radius:10px; text-align:center;">
                                <strong>📊 Severity</strong><br><span style="font-size:24px; font-weight:bold;">${{d.severity || 'Moderate'}}</span>
                            </div>
                            <div style="background:#f0f0f0; padding:15px; border-radius:10px; text-align:center;">
                                <strong>🚨 Emergency Risk</strong><br><span style="font-size:24px; font-weight:bold;">${{d.emergency_risk || 'Low'}}</span>
                            </div>
                        </div>
                        <p><strong>💊 Medicine Advice:</strong> ${{d.medicine || 'Consult a doctor for proper prescription'}}</p>
                        <p><strong>🏠 Home Care:</strong> ${{d.home_remedy || 'Rest and stay hydrated'}}</p>
                        <p><strong>👨‍⚕️ Recommended Specialist:</strong> ${{d.doctor_specialty || 'General Physician'}}</p>
                    `;
                    document.getElementById('result').innerHTML = html;
                    document.getElementById('result').style.display = 'block';
                    loadDoctors(location, d.primary_disease?.name);
                }} else {{
                    document.getElementById('result').innerHTML = '<p style="color:red;">Unable to analyze. Please provide more details.</p>';
                    document.getElementById('result').style.display = 'block';
                }}
            }} catch(e) {{
                document.getElementById('loading').style.display = 'none';
                document.getElementById('result').innerHTML = '<p style="color:red;">Error: ' + e.message + '</p>';
                document.getElementById('result').style.display = 'block';
            }}
        }}
        
        async function loadDoctors(location, disease) {{
            try {{
                const response = await fetch('/get-doctors', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ location: location, disease_name: disease || '', language: 'en' }})
                }});
                const data = await response.json();
                if (data.doctors && data.doctors.length > 0) {{
                    let html = '<div style="margin-top:20px;"><h3>👨‍⚕️ Recommended Doctors in ' + location + '</h3>';
                    data.doctors.forEach(doc => {{
                        html += `
                            <div class="doctor-card">
                                <strong>👨‍⚕️ ${{doc.name}}</strong><br>
                                🩺 ${{doc.specialty}}<br>
                                🏥 ${{doc.hospital}}<br>
                                📍 ${{doc.address}}<br>
                                💰 Fee: ${{doc.fee}}<br>
                                📞 ${{doc.contact}}<br>
                                ⏰ ${{doc.available}}<br>
                                ⭐ ${{doc.rating}} (${{doc.experience}})
                            </div>
                        `;
                    }});
                    html += '</div>';
                    document.getElementById('result').innerHTML += html;
                }}
            }} catch(e) {{
                console.log('Error loading doctors:', e);
            }}
        }}
    </script>
</body>
</html>'''

class SymptomRequest(BaseModel):
    symptoms: str
    age: Optional[int] = None
    gender: Optional[str] = None
    duration_value: Optional[int] = None
    duration_unit: Optional[str] = None
    location: Optional[str] = None
    language: str = "en"

def call_ai(prompt):
    if not OPENROUTER_API_KEY:
        return None
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={"model": "openai/gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "temperature": 0.4, "max_tokens": 4000},
            timeout=90
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except:
        pass
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
    return HTMLResponse(content=HTML_PAGE, status_code=200)

@app.head("/")
async def head():
    return HTMLResponse(content="", status_code=200)

@app.post("/analyze")
async def analyze(req: SymptomRequest):
    prompt = f"""You are an AI doctor. Diagnose based ONLY on these symptoms. NO predefined data.
Symptoms: {req.symptoms}
Location: {req.location if req.location else 'Bangladesh'}

Return ONLY JSON:
{{"primary_disease": {{"name": "disease name", "clinical_reasoning": "why this matches"}},
"severity": "Mild/Moderate/Severe", "emergency_risk": "Low/Medium/High",
"medicine": "medicine advice", "doctor_specialty": "specialist type", "home_remedy": "home care"}}"""
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
    prompt = f"""Recommend 4 realistic doctors in {location}, Bangladesh for {disease_name}. Return ONLY JSON:
{{"doctors": [{{"name": "Dr. Name", "specialty": "Specialty", "hospital": "Hospital", "address": "Address", "fee": "fee", "contact": "phone", "available": "time", "experience": "years", "rating": "4.5"}}]}}"""
    ai_response = call_ai(prompt)
    if ai_response:
        parsed = extract_json(ai_response)
        if parsed and "doctors" in parsed:
            return {"doctors": parsed["doctors"][:4]}
    return {"doctors": []}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)