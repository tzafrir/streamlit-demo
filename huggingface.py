"""
Hugging Face API Integration Module

This module provides functions to interact with Hugging Face's model inference API,
specifically for generating music and images using pre-trained models.

Models used:
    - facebook/musicgen-small: For music generation
    - black-forest-labs/FLUX.1-schnell: For fast image generation

Required Environment Variables:
    - HF_API_KEY: API key for accessing Hugging Face's inference API
"""

import requests
import os

HF_API_KEY = os.getenv("HF_API_KEY")

headers = {"Authorization": f"Bearer {HF_API_KEY}"}

def generate_music(prompt):
    """
    Generate music based on a text prompt using facebook/musicgen-small model.
    
    Args:
        prompt (str): Text description of the music to generate
        
    Returns:
        bytes: Generated audio data in binary format
        
    Note:
        Uses the musicgen-small model which is optimized for faster inference
        while maintaining reasonable quality.
    """
    api_url = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
    
    payload = {
        "inputs": prompt,
    }
    
    response = requests.post(api_url, headers=headers, json=payload)

    return response.content

def generate_image(prompt):
    """
    Generate an image based on a text prompt using FLUX.1-schnell model.
    
    Args:
        prompt (str): Text description of the image to generate
        
    Returns:
        bytes: Generated image data in binary format
        
    Note:
        Uses 4 inference steps for fast generation, optimized for speed
        over maximum quality.
    """
    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

    payload = {
        "inputs": prompt,
        "num_inference_steps": 4
    }

    response = requests.post(api_url, headers=headers, json=payload)

    return response.content
