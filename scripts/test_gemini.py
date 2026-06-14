import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
from dotenv import load_dotenv
load_dotenv()

from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Reply with exactly: OK",
)
print("Gemini says:", resp.text)