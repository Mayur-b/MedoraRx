"""Smoke test: Azure OpenAI GPT-4o connectivity."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from openai import AzureOpenAI

def test_openai():
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if not endpoint or not key:
        print("FAIL: AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_KEY not set in .env")
        sys.exit(1)

    try:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version="2024-12-01-preview",
        )
        response = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": "Say: MedoraRx is ready"}],
        )
        text = response.choices[0].message.content
        print(f"SUCCESS: GPT-4o responded: {text}")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_openai()
