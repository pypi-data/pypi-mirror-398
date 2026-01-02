#!/usr/bin/env python3
"""
Fetch model data from OpenAI, Anthropic, and Google Gemini APIs.
Saves raw responses to data/raw/ for Claude to process.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"


def fetch_openai_models() -> dict:
    """Fetch models from OpenAI API"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set", "models": []}

    try:
        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()

        # Filter to relevant models (GPT, o1, o3, etc.)
        relevant_prefixes = ("gpt-5", "gpt-4", "gpt-3.5", "o1", "o3", "o4", "chatgpt")
        models = [
            m for m in data.get("data", [])
            if any(m["id"].startswith(p) for p in relevant_prefixes)
        ]

        return {
            "provider": "openai",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "model_count": len(models),
            "models": sorted(models, key=lambda x: x.get("created", 0), reverse=True)
        }
    except Exception as e:
        return {"error": str(e), "models": []}


def fetch_anthropic_models() -> dict:
    """Fetch models from Anthropic API"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set", "models": []}

    try:
        response = httpx.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()

        return {
            "provider": "anthropic",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "model_count": len(data.get("data", [])),
            "models": data.get("data", [])
        }
    except Exception as e:
        return {"error": str(e), "models": []}


def fetch_google_models() -> dict:
    """Fetch models from Google Gemini API"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_API_KEY not set", "models": []}

    try:
        all_models = []
        next_page_token = None

        while True:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            if next_page_token:
                url += f"&pageToken={next_page_token}"

            response = httpx.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            all_models.extend(data.get("models", []))
            next_page_token = data.get("nextPageToken")

            if not next_page_token:
                break

        # Filter to Gemini models
        gemini_models = [m for m in all_models if "gemini" in m.get("name", "").lower()]

        return {
            "provider": "google",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "model_count": len(gemini_models),
            "models": gemini_models
        }
    except Exception as e:
        return {"error": str(e), "models": []}


def fetch_all() -> dict:
    """Fetch from all providers and save raw data"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching OpenAI models...")
    openai_data = fetch_openai_models()
    print(f"  Found {openai_data.get('model_count', 0)} models")

    print("Fetching Anthropic models...")
    anthropic_data = fetch_anthropic_models()
    print(f"  Found {anthropic_data.get('model_count', 0)} models")

    print("Fetching Google Gemini models...")
    google_data = fetch_google_models()
    print(f"  Found {google_data.get('model_count', 0)} models")

    # Save raw data
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with open(RAW_DIR / f"openai_{timestamp}.json", "w") as f:
        json.dump(openai_data, f, indent=2)

    with open(RAW_DIR / f"anthropic_{timestamp}.json", "w") as f:
        json.dump(anthropic_data, f, indent=2)

    with open(RAW_DIR / f"google_{timestamp}.json", "w") as f:
        json.dump(google_data, f, indent=2)

    # Also save combined raw data
    combined = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "openai": openai_data,
        "anthropic": anthropic_data,
        "google": google_data
    }

    with open(RAW_DIR / "latest.json", "w") as f:
        json.dump(combined, f, indent=2)

    print(f"\nRaw data saved to {RAW_DIR}")
    return combined


if __name__ == "__main__":
    fetch_all()
