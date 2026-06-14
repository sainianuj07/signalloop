import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.classify.prompt import build_prompt
from src.llm import complete, PROVIDER

example = "very laggy app plus website also feels very laggy"
prompt = build_prompt(example)

print(f"Provider: {PROVIDER}")
print("AI replied:")
print(complete(prompt))