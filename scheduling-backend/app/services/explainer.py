import os
from typing import List
from app.models.schemas import ConflictDetail

try:
    from google import genai
except ImportError:
    genai = None

class Explainer:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client() if self.api_key and genai else None

    def summarize_conflicts(self, conflicts: List[ConflictDetail]) -> str:
        if not conflicts:
            return "No conflicts detected."

        conflict_descriptions = [f"- {c.type}: {c.description}" for c in conflicts]
        prompt = f"Summarize these scheduling conflicts briefly:\n" + "\n".join(conflict_descriptions)

        if not self.client:
            return f"Found {len(conflicts)} conflict(s): " + ", ".join([c.type for c in conflicts])
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text
        except Exception:
            return f"Found {len(conflicts)} conflict(s): " + ", ".join([c.type for c in conflicts])

explainer_instance = Explainer()
