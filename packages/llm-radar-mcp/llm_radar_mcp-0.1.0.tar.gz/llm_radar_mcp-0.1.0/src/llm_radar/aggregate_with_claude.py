#!/usr/bin/env python3
"""
Use Claude (Anthropic API) to intelligently aggregate and enrich model data.
This script reads raw API responses and uses Claude to:
1. Normalize and structure the data
2. Add helpful descriptions and context
3. Generate a human-readable MODELS.md
4. Track what's new/changed since last update
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent  # src/llm_radar -> src -> project root
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

# NOTE: Pricing data removed - was manually maintained and became stale.
# Focus is now on API accessibility, not pricing.
# Users should check provider websites for current pricing.


def load_raw_data() -> dict:
    """Load the latest raw API data"""
    raw_file = RAW_DIR / "latest.json"
    if not raw_file.exists():
        raise FileNotFoundError(f"No raw data found at {raw_file}. Run fetch_models.py first.")

    with open(raw_file) as f:
        return json.load(f)


def load_previous_data() -> dict | None:
    """Load previous aggregated data for comparison"""
    models_file = DATA_DIR / "models.json"
    if models_file.exists():
        with open(models_file) as f:
            return json.load(f)
    return None


def aggregate_with_claude(raw_data: dict, previous_data: dict | None = None) -> tuple[dict, str]:
    """
    Use Claude to process raw API data into structured, enriched format.
    Returns (models_json, models_markdown)
    """
    client = anthropic.Anthropic()

    # Prepare context about previous data for change detection
    previous_context = ""
    if previous_data:
        prev_models = []
        for provider_data in previous_data.get("providers", {}).values():
            for m in provider_data.get("models", []):
                prev_models.append(f"{m.get('provider', 'unknown')}/{m.get('id', 'unknown')}")
        previous_context = f"\n\nPreviously tracked models: {', '.join(prev_models[:50])}"

    # Sort Google models to prioritize newest (Gemini 3 > 2.5 > 2.0 > 1.5)
    google_data = raw_data.get('google', {})
    if 'models' in google_data:
        def model_priority(m):
            name = m.get('name', '').lower()
            if 'gemini-3' in name: return 0
            if 'gemini-2.5' in name: return 1
            if 'gemini-2.0' in name or 'gemini-2-' in name: return 2
            if 'gemini-1.5' in name: return 3
            return 4
        google_data['models'] = sorted(google_data['models'], key=model_priority)

    prompt = f"""You are an AI model data curator. Your job is to help developers understand which models they can ACCESS via API.

CRITICAL: Only report FACTS from the raw API data. Do NOT infer or guess capabilities, context windows, or features.

## Raw API Data

### OpenAI Models
```json
{json.dumps(raw_data.get('openai', {}), indent=2)[:12000]}
```

### Anthropic Models
```json
{json.dumps(raw_data.get('anthropic', {}), indent=2)[:8000]}
```

### Google Gemini Models
```json
{json.dumps(google_data, indent=2)[:12000]}
```
{previous_context}

## Your Task

Create a JSON object with this structure:
```json
{{
  "updated_at": "<current ISO timestamp>",
  "summary": "<1-2 sentence factual summary of models available>",
  "providers": {{
    "openai": {{
      "name": "OpenAI",
      "website": "https://openai.com",
      "api_docs": "https://platform.openai.com/docs",
      "models": [
        {{
          "id": "<exact model id from API - this is what developers use>",
          "name": "<human-friendly name>",
          "provider": "openai",
          "api_accessible": true,
          "model_type": "<chat|completion|embedding|image|audio|other>",
          "description": "<1 sentence based on model name only, no guessing>",
          "context_window": <only if explicitly in API data, otherwise null>,
          "input_modalities": ["text"] or ["text", "image"] <only if KNOWN from API>,
          "output_modalities": ["text"] <only if KNOWN from API>,
          "status": "<active|preview|deprecated - based on model name hints like 'preview', 'exp'>",
          "created_timestamp": <unix timestamp from API if available>,
          "owned_by": "<from API data>"
        }}
      ]
    }},
    "anthropic": {{ ... }},
    "google": {{ ... }}
  }}
}}
```

## STRICT Guidelines

1. **API Accessible**: All models from these API responses ARE accessible. Set `api_accessible: true`.

2. **Model Selection**:
   - INCLUDE: All chat/completion models (gpt-*, claude-*, gemini-*)
   - INCLUDE: Reasoning models (o1, o3, o4)
   - SKIP: Fine-tune models (ft:*), embedding models (*-embedding-*), internal models
   - SKIP: Models with "instruct" suffix (these are older)
   - SKIP: Dated versions if a base version exists (e.g., skip gpt-4o-2024-08-06 if gpt-4o exists)

3. **Model Type Classification**:
   - "chat" = conversational models (gpt-4*, claude-*, gemini-*)
   - "reasoning" = o-series models (o1, o3, o4)
   - "image" = image generation (dall-e, imagen)
   - "audio" = audio/speech models (tts, whisper, transcribe)
   - "embedding" = embedding models

4. **DO NOT INFER**:
   - Do NOT guess context windows - use null unless explicitly in API
   - Do NOT guess capabilities - only use what's in the API response
   - Do NOT add pricing - we don't have reliable data
   - Do NOT invent release dates - use created_timestamp only

5. **Modalities**: Only set if clearly indicated by model name:
   - "*-vision*" or "4o" = input: ["text", "image"]
   - "*-audio*" or "*realtime*" = involves audio
   - Otherwise just ["text"]

6. Current date: {datetime.now(timezone.utc).strftime("%Y-%m-%d")}

Output ONLY valid JSON, no markdown code blocks or explanations."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse Claude's response
    json_text = response.content[0].text.strip()
    # Remove any markdown code blocks if present
    if json_text.startswith("```"):
        json_text = json_text.split("```")[1]
        if json_text.startswith("json"):
            json_text = json_text[4:]
    if json_text.endswith("```"):
        json_text = json_text[:-3]

    models_data = json.loads(json_text.strip())

    # Now generate the markdown version
    markdown = generate_markdown(models_data)

    return models_data, markdown


def generate_markdown(data: dict) -> str:
    """Generate a clean MODELS.md from the structured data"""
    client = anthropic.Anthropic()

    prompt = f"""Generate a clean, developer-focused Markdown document showing available AI models.

Data:
```json
{json.dumps(data, indent=2)}
```

Create a MODELS.md with:
1. Header with update date and summary
2. Quick reference table per provider showing: Model ID, Type, Status
3. The Model ID should be the exact string developers use in API calls
4. Group by provider (OpenAI, Anthropic, Google)
5. Note which models support multimodal input (images, audio)

Keep it factual and scannable. No marketing language. Developers need to quickly find model IDs they can use.

Output ONLY the markdown content."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()


def save_outputs(models_data: dict, markdown: str):
    """Save the processed data"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save JSON
    with open(DATA_DIR / "models.json", "w") as f:
        json.dump(models_data, f, indent=2)
    print(f"Saved {DATA_DIR / 'models.json'}")

    # Save Markdown
    with open(DATA_DIR / "MODELS.md", "w") as f:
        f.write(markdown)
    print(f"Saved {DATA_DIR / 'MODELS.md'}")


def main():
    print("Loading raw API data...")
    raw_data = load_raw_data()

    print("Loading previous data for comparison...")
    previous_data = load_previous_data()

    print("Asking Claude to aggregate and enrich the data...")
    models_data, markdown = aggregate_with_claude(raw_data, previous_data)

    print("Saving outputs...")
    save_outputs(models_data, markdown)

    print(f"\nDone! Summary: {models_data.get('summary', 'No summary')}")


if __name__ == "__main__":
    main()
