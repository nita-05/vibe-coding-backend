#!/usr/bin/env python3
"""
Simple script to validate OpenAI API key.
Usage: python check_openai_key.py [API_KEY]
If no API key is provided, it will try to load from .env file.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from openai import OpenAI
    from app.config import settings
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Make sure you're in the backend directory and dependencies are installed.")
    sys.exit(1)


def validate_api_key(api_key: str = None) -> bool:
    """
    Validate OpenAI API key by making a simple API call.
    
    Args:
        api_key: OpenAI API key. If None, loads from settings.
    
    Returns:
        True if key is valid, False otherwise.
    """
    if api_key is None:
        try:
            api_key = settings.openai_api_key
        except Exception as e:
            print(f"[ERROR] Error loading API key from .env: {e}")
            return False
    
    if not api_key or api_key.strip() == "":
        print("[ERROR] API key is empty!")
        return False
    
    # Check if it looks like a valid OpenAI key format
    if not api_key.startswith("sk-"):
        print("[WARNING] API key doesn't start with 'sk-' (might be invalid format)")
    
    try:
        # Create OpenAI client
        client = OpenAI(api_key=api_key, timeout=10.0)
        
        # Make a simple, cheap API call to validate the key
        # Using models.list() is a good way to test without spending credits
        print("Testing API key...")
        response = client.models.list()
        
        # If we get here without exception, the key is valid
        print("[SUCCESS] API key is VALID!")
        print(f"   Key starts with: {api_key[:7]}...{api_key[-4:]}")
        print(f"   You have access to {len(list(response))} models")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "Incorrect API key" in error_msg or "Invalid API key" in error_msg:
            print("[ERROR] API key is INVALID!")
            print("   The API key provided is not recognized by OpenAI.")
        elif "Insufficient quota" in error_msg or "You exceeded your current quota" in error_msg:
            print("[WARNING] API key is valid but QUOTA EXCEEDED!")
            print("   You need to add credits to your OpenAI account.")
        elif "rate limit" in error_msg.lower():
            print("[WARNING] API key is valid but RATE LIMITED!")
            print("   Too many requests. Try again later.")
        else:
            print(f"[ERROR] Error validating API key: {error_msg}")
        return False


if __name__ == "__main__":
    # Check if API key provided as command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"Testing provided API key: {api_key[:7]}...{api_key[-4:]}")
        is_valid = validate_api_key(api_key)
    else:
        print("No API key provided, loading from .env file...")
        is_valid = validate_api_key()
    
    sys.exit(0 if is_valid else 1)




