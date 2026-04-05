import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
if not key:
    print("No GEMINI_API_KEY found in .env mapping!")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
response = requests.get(url)

if response.status_code == 200:
    print("Successfully fetched Models List:\n")
    for model in response.json().get("models", []):
        methods = model.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            print(f"- {model['name']}")
else:
    print("Error calling API:", response.status_code, response.text)
