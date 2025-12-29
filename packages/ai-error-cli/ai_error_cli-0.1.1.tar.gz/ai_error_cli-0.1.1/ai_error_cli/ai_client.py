import requests
from .config import AI_API_URL, TIMEOUT, MAX_RETRIES, RETRY_DELAY
import time
import sys

def send_error_to_ai(error_text: str) -> dict:
    payload = {"error": error_text}

    print("⏳ Contacting AI service...", file=sys.stderr)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                AI_API_URL,
                json=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()

            ai_response = response.json()

            # ❗ Ensure AI returned something useful
            if not ai_response or not any(ai_response.values()):
                raise ValueError("Empty AI response")

            return ai_response  # ✅ FINAL RETURN

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(
                    f"🔁 Retry {attempt}/{MAX_RETRIES} — temporary issue, trying again...",
                    file=sys.stderr
                )
                time.sleep(RETRY_DELAY)
            else:
                print(
                    "❌ AI service unavailable after multiple attempts.",
                    file=sys.stderr
                )
                return {
                    "cause": "AI service unavailable after retries.",
                    "solution": "Please retry later or ensure the AI backend is running.",
                    "example": str(e),
                    "category": "Unknown",
                    "confidence": 0.0,
                }

