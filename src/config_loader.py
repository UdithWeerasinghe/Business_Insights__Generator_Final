# src/config_loader.py
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file.
load_dotenv()

def get_hf_api_key():
    return os.getenv("HF_API_KEY")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print("Hugging Face API Key:", get_hf_api_key())
