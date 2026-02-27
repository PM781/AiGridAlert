# backend/data_assets.py

# Complete mapping of 15 Disasters and their Checklists
RISK_CATEGORIES = {
    "Natural": {
        "Flood": ["River flooding", "Urban flooding", "Flash floods", "Dam overflow"],
        "Landslide": ["Hill slope collapse", "Road blockage", "House burial"],
        "Forest Fire": ["Dry-season fire", "Wildlife habitat fire", "Smoke inhalation"],
        "Cyclone": ["Strong winds", "Coastal flooding", "Storm surge"],
        "Drought": ["Crop failure", "Water scarcity", "Heat stress"]
    },
    "Infrastructure": {
        "Building Collapse": ["People trapped", "Adjacent building risk", "Gas leak"],
        "Bridge Collapse": ["Structural failure", "Traffic cut off", "Vehicles submerged"],
        "Road Damage": ["Sinkhole detected", "Vehicle trapped", "Main highway cut off"],
        "Dam Risk": ["Leakage", "Structural crack", "Downstream evacuation"],
        "Power Grid": ["Power failure", "Communication failure", "Hospital backup status"]
    },
    "Medical_Human": {
        "Medical": ["Injury (Bleeding)", "Unconscious", "Chronic patient risk"],
        "Industrial Leak": ["Chemical leak", "Gas explosion risk", "Evacuation zone"],
        "Explosion": ["Explosion", "Secondary fire", "Shattered glass risk"],
        "Urban Fire": ["Urban fire", "Fire exit blocked", "Smoke inhalation"],
        "Accident": ["Major accident", "People trapped", "Fuel leak"]
    }
}

RESOURCES = {
    "Medical Team": "5 Units Active (SDRF HQ)",
    "Rescue Boat": "3 Units Active (Coastal Command)",
    "Food Supply": "12 Units (KSDMA Warehouse)",
    "SDRF Squad": "2 Rapid Response Teams",
    "Power Repair": "4 Technical Units"
}

VULNERABLE_KEYWORDS = ["elderly", "child", "pregnant", "disabled", "infant", "injured", "trapped", "bleeding", "unconscious", "oxygen"]

def calculate_hybrid_weight(ai_score, raw_text, district, disaster_type, risk_data):
    """Calculates Final Severity with specific priority boosts."""
    score = float(ai_score)
    text_lower = raw_text.lower()
    
    # Life-threat boost (+2.5)
    if any(word in text_lower for word in VULNERABLE_KEYWORDS):
        score += 2.5
        
    # Regional Hazard boost (+1.0)
    district_info = risk_data.get(district, "").lower()
    if disaster_type.lower() in district_info:
        score += 1.0
        
    return min(round(score, 1), 10.0)