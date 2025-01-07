"""
Supabase client setup and token tracking functionality.
"""

from supabase import create_client
import os
from datetime import datetime

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def track_token_usage(prompt_tokens, completion_tokens, model="gpt-4o"):
    """
    Track token usage for a chat completion request.
    
    Args:
        prompt_tokens (int): Number of tokens in the prompt
        completion_tokens (int): Number of tokens in the completion
        model (str): The model used for the completion
    """
    try:
        # Insert usage data
        supabase.table('token_usage').insert({
            'timestamp': datetime.utcnow().isoformat(),
            'model': model,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens
        }).execute()
    except Exception as e:
        print(f"Error tracking token usage: {str(e)}")

def get_total_tokens():
    """
    Get total token usage across all time.
    
    Returns:
        tuple: (prompt_tokens, completion_tokens) across all time
    """
    try:
        response = supabase.table('token_usage')\
            .select('prompt_tokens,completion_tokens')\
            .execute()
        
        prompt_tokens = sum(row['prompt_tokens'] for row in response.data)
        completion_tokens = sum(row['completion_tokens'] for row in response.data)
        return prompt_tokens, completion_tokens
    except Exception as e:
        print(f"Error getting total tokens: {str(e)}")
        return 0, 0 