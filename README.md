# 🚀 FastAPI in Google Colab (Localhost)

Run a **FastAPI server directly inside Google Colab**, make API calls from within Colab, and manage server processes seamlessly.  
This setup is ideal for **prototyping APIs, testing ML models**, and integrating with tools like Gradio or Hugging Face.

---

## 📂 Project Structure
project/
│
├── app/
│ ├── init.py
│ └── api.py # FastAPI app definition
│
├── main_colab.py # Script to manage server & API calls
└── requirements.txt # Dependencies

---

## 🛠️ Installation

In a Colab cell, run:
pip install fastapi uvicorn nest_asyncio psutil requests
🖥️ API Details
Base URL (Localhost in Colab):

http://127.0.0.1:8000
POST /brief
Generates a mock "brief" based on given parameters.

Request Body
{
  "topic": "string",
  "depth": 2,
  "follow_up": false,
  "user_id": "u1"
}
Example Response
{
  "message": "Brief generated successfully!",
  "data": {
    "topic": "LLM evaluation methods in production",
    "depth": 2,
    "follow_up": false,
    "user_id": "u1"
  }
}
▶️ How to Run in Google Colab
1️⃣ Create the FastAPI App

!mkdir -p app
!touch app/__init__.py

%%writefile app/api.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class BriefRequest(BaseModel):
    topic: str
    depth: int
    follow_up: bool
    user_id: str

@app.post("/brief")
async def brief(request: BriefRequest):
    return {
        "message": "Brief generated successfully!",
        "data": request.dict()
    }
2️⃣ Start the FastAPI Server

import subprocess, time, requests, json, os, signal, psutil, nest_asyncio
nest_asyncio.apply()

# Kill any existing uvicorn processes to avoid conflicts
for p in psutil.process_iter(attrs=["pid","name","cmdline"]):
    try:
        if p.info["cmdline"] and "uvicorn" in " ".join(p.info["cmdline"]):
            os.kill(p.info["pid"], signal.SIGKILL)
    except Exception:
        pass

# Start FastAPI server
server = subprocess.Popen(
    ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
time.sleep(3)  # Allow server time to start
3️⃣ Send a Test Request

payload = {
    "topic": "LLM evaluation methods in production",
    "depth": 2,
    "follow_up": False,
    "user_id": "u1"
}
response = requests.post("http://127.0.0.1:8000/brief", json=payload, timeout=180)
print("Status:", response.status_code)
print(json.dumps(response.json(), indent=2))
⚠️ Troubleshooting
1. Module Not Found

ERROR: Could not import module "app.api"
✅ Ensure app/api.py exists and contains app = FastAPI().

2. Connection Refused

ConnectionRefusedError: [Errno 111] Connection refused
✅ Increase time.sleep(3) in the server start cell.

📚 Features
Run FastAPI directly inside Google Colab

Automatically kills previous server instances to prevent port conflicts

Uses Pydantic for request validation

Easily extendable to multiple endpoints

🚀 Next Steps
Add a Gradio UI for live interaction

Integrate Hugging Face models for AI-powered endpoints

Make the API public with ngrok or Hugging Face Spaces

📜 License
This project is licensed under the MIT License.
