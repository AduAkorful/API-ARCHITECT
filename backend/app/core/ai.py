import google.generativeai as genai
import json
from backend.app.core.config import settings

# Configure the Gemini API client
genai.configure(api_key=settings.GEMINI_API_KEY)

# --- The System Prompt ---
# (This remains unchanged)
SYSTEM_PROMPT = """
You are "API Architect," an expert at converting natural language into a structured JSON representation for a simple REST API microservice. Your sole purpose is to generate a JSON object that conforms to the rules below. You must not add any commentary or introductory text. Only the JSON object is allowed.

JSON OUTPUT RULES:
1.  The top-level object must have two keys: "service_name" and "endpoint".
2.  "service_name" must be a DNS-compliant string (lowercase, numbers, hyphens) derived from the user's prompt, up to 30 characters. E.g., "contact form api" -> "contact-form-api".
3.  "endpoint" must be an object with the following keys: "path", "method", "model_name", "schema_fields".
4.  "path" must start with a "/" and be a valid URL path.
5.  "method" must be one of "GET", "POST", "PUT", "DELETE".
6.  "model_name" must be a valid Python class name in PascalCase. E.g., "ContactForm" or "WebhookPayload".
7.  "schema_fields" must be an array of objects.
8.  Each object in "schema_fields" must have three keys: "name" (string, snake_case), "type" (string), "required" (boolean).
9.  The "type" for a schema field must be a valid Pydantic type. Prioritize these common types:
    - str
    - int
    - float
    - bool
    - EmailStr (use this for any field that looks like an email address)
    - List[str]
    - List[int]
    - Dict[str, Any]
10. If the user does not specify if a field is required, assume it is "true" for POST/PUT requests.
"""

def generate_spec_from_prompt(prompt: str) -> dict:
    """
    Sends a user prompt to the Gemini API and returns the generated JSON spec.
    """
    try:
        model = genai.GenerativeModel(
            # --- THE DEFINITIVE FIX ---
            # Use the exact model name confirmed by our diagnostic script.
            model_name='models/gemini-pro-latest',
            system_instruction=SYSTEM_PROMPT
        )
        response = model.generate_content(prompt)
        
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()

        if not cleaned_response:
            raise ValueError("AI model returned an empty response.")

        spec = json.loads(cleaned_response)
        return spec

    except json.JSONDecodeError:
        raise ValueError(f"Failed to decode JSON from the AI model's response. Raw response: '{response.text}'")
    except Exception as e:
        print(f"An unexpected error occurred in the AI module: {e}")
        raise