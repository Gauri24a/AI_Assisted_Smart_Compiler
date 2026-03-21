import os
import google.generativeai as genai

# Load env
def load_env():
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip()

load_env()

api_key = os.getenv('GEMINI_API_KEYS')
model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

if not api_key:
    print("No API key")
    exit(1)

genai.configure(api_key=api_key)

try:
    models = genai.list_models()
    print("Available models:")
    for model in models:
        print(f"  {model.name}")
    # Try to generate
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello")
    print("API key valid. Response:", response.text[:100])
except Exception as e:
    print("API key invalid or error:", str(e))