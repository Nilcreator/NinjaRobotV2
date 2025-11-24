import google.generativeai as genai
import os

# --- IMPORTANT: CONFIGURE YOUR API KEY ---
# Option 1: Set as an environment variable (recommended)
# Ensure you've run 'export GOOGLE_API_KEY="YOUR_API_KEY"' in your terminal
# or set it in your .bashrc and sourced it.
# api_key = os.getenv("GOOGLE_API_KEY")

# Option 2: Hardcode it here for a quick test (NOT FOR PRODUCTION)
# Replace "YOUR_API_KEY" with your actual key.
api_key = "Input your Google API Key Here!" # <<< REPLACE THIS WITH YOUR ACTUAL API KEY

if not api_key:
    print("Error: GOOGLE_API_KEY not found.")
    print("Please set the GOOGLE_API_KEY environment variable or hardcode it in the script.")
    exit()

try:
    genai.configure(api_key=api_key)

    print("Fetching available Gemini models...\n")
    for model in genai.list_models():
        # We are interested in models that support 'generateContent' (text generation)
        # and potentially 'embedContent' (for embeddings) or other methods.
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model Name: {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print(f"  Supported Generation Methods: {model.supported_generation_methods}")
            # You can print other attributes like model.version, model.input_token_limit, etc.
            print("-" * 30)

except Exception as e:
    print(f"An error occurred: {e}")
    print("Please ensure your API key is correct, valid, and has the Gemini API enabled in your Google Cloud project.")
