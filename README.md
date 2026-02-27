# AiGridAlert | Karnataka Emergency Dispatch Command

**AiGridAlert** is an AI-powered triage and dispatch dashboard designed for the Karnataka Division. It uses Gemini AI to analyze field reports and recommend specific rescue units (SDRF/Fire/Medical) based on severity and local risk data.

## 🚀 Features
* **15 Disaster Categories**: Tailored for regional risks like Landslides and Floods.
* **Hybrid Triage**: Combines AI analysis with manual operator verification checklists.
* **Incident Site Tracking**: Allows manual entry of precise landmarks for dispatchers.
* **Mission History**: Persistently logs all triaged alerts for post-incident review.

## 🛠️ Tech Stack
* **Frontend**: Tailwind CSS, FontAwesome, JavaScript (ES6).
* **Backend**: FastAPI, Uvicorn, Pydantic.
* **AI**: Google Gemini 1.5 Flash.

## ⚙️ Installation
1. Clone the repo: `git clone <your-url>`
2. Install requirements: `pip install -r requirements.txt`
3. Create a `.env` file and add: `GEMINI_API_KEY=your_key_here`
4. Start the server: `$env:PYTHONPATH="."; uvicorn backend.main:app --reload`