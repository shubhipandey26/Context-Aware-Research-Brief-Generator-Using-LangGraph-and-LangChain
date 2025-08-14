#🚀 FastAPI in Google Colab – Local API Development
Run a fully functional FastAPI server directly inside Google Colab without any external hosting.
This project sets up a local development environment for testing APIs, integrating ML models, and connecting with Gradio or Hugging Face for rapid prototyping.
---
#📌 Features
✅ Run FastAPI in Google Colab without needing a cloud VM or deployment.
✅ Automatic process management – kills existing uvicorn processes before starting.
✅ Local API endpoint testing with requests.
✅ Ready-to-use structure for ML/AI project integration.
✅ Easy to extend with Gradio UI or Hugging Face Spaces.
---
#📂 Project Structure
project-root/
│
├── app/
│   ├── __init__.py
│   ├── api.py         # Main FastAPI app
│   └── utils.py       # Optional helper functions
│
├── requirements.txt   # Python dependencies
├── main.ipynb         # Google Colab Notebook
└── README.md          # Project documentation
---
⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/your-username/fastapi-colab.git
cd fastapi-colab
2️⃣ Install dependencies
pip install -r requirements.txt
3️⃣ Run in Google Colab
Upload the project files to your Colab environment.
Open main.ipynb in Colab.
Execute all cells to start the FastAPI server.
API will be accessible at:
http://127.0.0.1:8000
---
🖥 Example API Call
Once the server is running, test it with:
import requests, json
payload = {
    "topic": "LLM evaluation methods in production",
    "depth": 2,
    "follow_up": False,
    "user_id": "u1"
}
response = requests.post("http://127.0.0.1:8000/brief", json=payload)
print(json.dumps(response.json(), indent=2))
---
📜 Example API Response
{
  "summary": "This is a generated brief about LLM evaluation methods in production...",
  "topic": "LLM evaluation methods in production",
  "depth": 2
}
---
📌 Requirements
Python 3.9+
Google Colab environment
FastAPI, Uvicorn, psutil, nest_asyncio, requests
---
🔗 Useful Links
FastAPI Documentation
Gradio Documentation
Hugging Face Spaces
---
📄 License
This project is licensed under the MIT License – feel free to modify and use for your own projects.
---
