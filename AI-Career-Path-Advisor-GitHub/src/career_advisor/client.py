import os
from openai import OpenAI

def create_client() -> OpenAI:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY was not found. Set it as an environment variable.")
    return OpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
