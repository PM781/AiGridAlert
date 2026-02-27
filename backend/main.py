import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from dotenv import load_dotenv

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("❌ GEMINI_API_KEY not found in environment variables!")
else:
    print("✅ Gemini API Key Loaded Successfully")

# -----------------------------
# Initialize Gemini Client
# -----------------------------
client = genai.Client(api_key=GEMINI_KEY)

app = FastAPI()

# -----------------------------
# Enable CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Import Local Assets
# -----------------------------
try:
    from .data_assets import calculate_hybrid_weight, RESOURCES, RISK_CATEGORIES
except ImportError:
    import data_assets
    calculate_hybrid_weight = data_assets.calculate_hybrid_weight
    RESOURCES = data_assets.RESOURCES
    RISK_CATEGORIES = data_assets.RISK_CATEGORIES

# -----------------------------
# Load District Risk Data
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

try:
    with open(os.path.join(BASE_DIR, "data", "district_risk.json"), "r") as f:
        DISTRICT_RISK = json.load(f)
except Exception as e:
    print("⚠️ Could not load district_risk.json:", e)
    DISTRICT_RISK = {}

# -----------------------------
# Stable Model Selection
# -----------------------------
ACTIVE_MODEL = "models/gemini-2.5-flash"

# -----------------------------
# Analyze Endpoint
# -----------------------------
@app.post("/analyze")
async def analyze_incident(data: dict):
    try:
        user_text = data.get("text", "")
        manual_loc = data.get("manual_location", "")

        if not user_text:
            raise HTTPException(status_code=400, detail="No report text provided")

        # Flatten risk categories safely
        categories = []
        for cat in RISK_CATEGORIES.values():
            if isinstance(cat, dict):
                categories.extend(cat.keys())
            elif isinstance(cat, list):
                categories.extend(cat)

        prompt = f"""
        Act as a Karnataka Disaster Triage Officer.

        Analyze Report: "{user_text}"
        Manual Site Context: "{manual_loc}"

        Classify into EXACTLY one category from:
        {categories}

        Return JSON with:
        - disaster_type
        - district
        - location
        - severity (1-10 integer)
        - summary (1 sentence)
        - recommended_unit (choose from {list(RESOURCES.keys())})

        Return ONLY valid JSON.
        """

        response = client.models.generate_content(
            model=ACTIVE_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        raw_text = response.text.strip()

        # Clean accidental markdown formatting
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        print("🔎 RAW GEMINI OUTPUT:", raw_text)

        ai_output = json.loads(raw_text)

        # Manual location override
        if manual_loc:
            ai_output["location"] = manual_loc

        # Hybrid severity refinement
        ai_output["final_severity"] = calculate_hybrid_weight(
            ai_output.get("severity", 5),
            user_text,
            ai_output.get("district", "Unknown"),
            ai_output.get("disaster_type", "General"),
            DISTRICT_RISK
        )

        # Checklist extraction
        d_type = ai_output.get("disaster_type")
        checklist = []

        for cat in RISK_CATEGORIES.values():
            if isinstance(cat, dict) and d_type in cat:
                checklist = cat[d_type]
                break

        ai_output["checklist"] = checklist if checklist else [
            "Area Secured",
            "People Evacuated"
        ]

        # Resource status
        rec_unit = ai_output.get("recommended_unit", "SDRF Alpha Team")
        ai_output["recommended_unit"] = rec_unit
        ai_output["resource_status"] = RESOURCES.get(rec_unit, "Units on Standby")

        return ai_output

    except Exception as e:
        print("🚨 CRITICAL DISPATCH ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Static Frontend Mount
# -----------------------------
static_path = os.path.join(BASE_DIR, "static")
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")