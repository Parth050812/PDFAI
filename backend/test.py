import os
from google import genai
from dotenv import load_dotenv

# Load GEMINI_API_KEY from .env
load_dotenv()

# Initialize the Client
client = genai.Client()


def list_all_models():
    """Lists all models accessible by your API key."""
    print("=== All Available Models ===\n")
    for model in client.models.list():
        print(f"Name: {model.name}")
        print(f"Display Name: {model.display_name}")
        # The new SDK attribute is 'supported_actions'
        print(f"Supported Actions: {model.supported_actions}")
        print("-" * 50)


def list_models_by_capability():
    """Filters models based on supported actions."""
    print("\n=== Models for Text Generation (generateContent) ===")
    for model in client.models.list():
        if model.supported_actions and "generateContent" in model.supported_actions:
            print(f"- {model.name} ({model.display_name})")

    print("\n=== Models for Embeddings (embedContent) ===")
    for model in client.models.list():
        if model.supported_actions and "embedContent" in model.supported_actions:
            print(f"- {model.name} ({model.display_name})")


if __name__ == "__main__":
    list_all_models()
    list_models_by_capability()