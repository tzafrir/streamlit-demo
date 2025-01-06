import requests
import os

HF_API_KEY = os.getenv("HF_API_KEY")

headers = {"Authorization": f"Bearer {HF_API_KEY}"}

def generate_music(prompt):
    api_url = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
    
    payload = {
        "inputs": prompt,
    }
    
    response = requests.post(api_url, headers=headers, json=payload)

    return response.content

def generate_image(prompt):
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

    payload = {
        "inputs": prompt,
        "num_inference_steps": 4
    }

    response = requests.post(api_url, headers=headers, json=payload)

    return response.content
