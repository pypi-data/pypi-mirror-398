import requests
import json
import re

FREE_LLM_URL = "https://apifreellm.com/api/chat"

def explain_error(error_text: str) -> dict:
    """
    Sends error text to a free LLM API and returns a structured explanation.
    """

    # Construct prompt to ask the LLM to respond in JSON form
    prompt = f"""
You are an expert Python debugging assistant.

Analyze the following Python runtime error and respond ONLY in valid JSON.
Do NOT include explanations outside the JSON.

Required JSON format:
{{
  "cause": "<short clear explanation>",
  "solutions": ["step 1", "step 2", "..."],
  "example": "<before and after code>",
  "error_type": "<TypeError | KeyError | ImportError | etc>",
  "confidence": "<0.0–1.0, AI reliability score>",
  "possible_fix_steps": ["detailed step-by-step fixes"],
  "references": ["link1", "link2"],
  "preventive_tips": ["tips to avoid this error in future"],
  "code_context": "<optional code snippet if helpful>"
}}

Error:
{error_text}
"""

    try:
        response = requests.post(
            FREE_LLM_URL,
            json={"message": prompt},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "")
        print(text)

        # Try to convert LLM text into JSON
        return parse_llm_response(text)

    except Exception as e:
        return {
            "cause": "Failed to get AI response",
            "solution": "The free LLM service may be unavailable or rate-limited",
            "example": str(e),
        }


def parse_llm_response(content: str) -> dict:
    """
    Extracts JSON from LLM output and normalizes fields
    to always return clean strings.
    """

    try:
        # 🔹 Step 1: Extract JSON block using regex
        json_match = re.search(r"\{[\s\S]*\}", content)

        if not json_match:
            raise ValueError("No JSON found in LLM response")

        json_text = json_match.group()

        # 🔹 Step 2: Load JSON safely
        data = json.loads(json_text)

        # 🔹 Step 3: Normalize fields
        cause = str(data.get("cause", "")).strip()
        solution = str(data.get("solution", "")).strip()
        example_data = data.get("example", "")
        if isinstance(example_data, dict):
            # Convert nested example object to readable text
            example = "\n".join(
                f"{k}: {v}" for k, v in example_data.items()
            )
        else:
            example = str(example_data)

        return {
            "cause": cause,
            "solutions": data.get("solutions", []),
            "example": example,
            "error_type": str(data.get("error_type", "")).strip(),
            "confidence": float(data.get("confidence", 0.0)),
            "possible_fix_steps": data.get("possible_fix_steps", []),
            "references": data.get("references", []),
            "preventive_tips": data.get("preventive_tips", []),
            "code_context": str(data.get("code_context", "")).strip(),
        }

    except Exception as e:
        # 🔹 Step 4: Fallback (never break API)
        return {
            "cause": "AI response could not be parsed cleanly.",
            "solution": "Try simplifying the error or retry.",
            "example": f"Raw response: {content[:200]}..."
        }
