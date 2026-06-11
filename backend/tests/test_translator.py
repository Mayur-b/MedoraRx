"""Smoke test: Azure Translator connectivity (multi-service Azure AI Services resource)."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

TEXT = "The patient should take artemisinin daily."

def test_translator():
    key = os.getenv("AZURE_TRANSLATOR_KEY")
    region = os.getenv("AZURE_TRANSLATOR_REGION")

    if not key or not region:
        print("FAIL: AZURE_TRANSLATOR_KEY or AZURE_TRANSLATOR_REGION not set in .env")
        sys.exit(1)

    try:
        # Multi-service resources: pass region= so the SDK injects Ocp-Apim-Subscription-Region
        client = TextTranslationClient(
            credential=AzureKeyCredential(key),
            region=region,
        )
        results = client.translate(body=[TEXT], to_language=["hi"])
        translated = results[0].translations[0].text
        print(f"SUCCESS: Translated text: {translated}")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_translator()
