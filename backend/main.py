import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from dotenv import load_dotenv

# Relative imports to fix ModuleNotFoundError
try:
    from .data_assets import calculate_hybrid_weight, RESOURCES, RISK_CATEGORIES
except ImportError:
    import data_assets
    calculate_hybrid_weight = data_assets.calculate_hybrid_weight
    RESOURCES = data_assets.RESOURCES
    RISK_CATEGORIES = data_assets.RISK_CATEGORIES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load risk data
with open(os.path.join(BASE_DIR, "data", "district_risk.json"), "r") as f:
    DISTRICT_RISK = json.load(f)

@app.post("/analyze")
async def analyze_incident(data: dict):
    user_text = data.get("text")
    # Capture the manual location from your new frontend field
    manual_loc = data.get("manual_location", "") 
    
    # Updated Prompt to include manual location context
    categories = []
    for cat in RISK_CATEGORIES.values(): categories.extend(cat.keys())
    
    prompt = f"""
    Act as a Karnataka Triage Officer. 
    Analyze Report: "{user_text}"
    Manual Site Context: "{manual_loc}"
    
    Classify into EXACTLY one category: {categories}.
    Identify District, Precise Location, Severity (1-10), and a 1-sentence Summary.
    Identify the most appropriate 'recommended_unit' from this list: {list(RESOURCES.keys())}.
    Return ONLY valid JSON.
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # Ensure no extra spaces or hidden characters
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        ai_output = json.loads(response.text)
        
        # Override with manual location if provided
        if manual_loc:
            ai_output['location'] = manual_loc

        # 1. Refine Severity with Safety Fallbacks
        ai_output['final_severity'] = calculate_hybrid_weight(
            ai_output.get('severity', 5), 
            user_text, 
            ai_output.get('district', 'Unknown'), 
            ai_output.get('disaster_type', 'General'), 
            DISTRICT_RISK
        )
        
        # 2. Extract Checklist based on Category
        d_type = ai_output.get('disaster_type')
        checklist = []
        for cat in RISK_CATEGORIES.values():
            if d_type in cat:
                checklist = cat[d_type]
                break
        ai_output['checklist'] = checklist if checklist else ["Area Secured", "People Evacuated"]

        # 3. Resource Safety Check (Prevents 500 Error if unit key is missing)
        rec_unit = ai_output.get('recommended_unit', 'SDRF Alpha Team')
        ai_output['recommended_unit'] = rec_unit
        ai_output['resource_status'] = RESOURCES.get(rec_unit, "Units on Standby")
        
        return ai_output

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}") # Log to your terminal
        raise HTTPException(status_code=500, detail=str(e))

# Static mounting remains at the very end
static_path = os.path.join(BASE_DIR, "static")
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")