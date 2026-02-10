#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GROQ_API_KEY')
print(f"API Key loaded: {api_key[:20]}...{api_key[-10:]}")

# Initialize Groq client
try:
    client = Groq(api_key=api_key)
    print("✓ Groq client initialized successfully")
    
    # Test with simple message
    print("\nTesting API connection...")
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Say hello briefly"}
        ],
        model="llama-3.3-70b-versatile",
        max_tokens=50,
        temperature=0.3
    )
    
    response = chat_completion.choices[0].message.content
    print(f"✓ API Response: {response}")
    print("\n✓ Groq API Key is VALID and WORKING!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nThe API key might not be activated yet.")
    print("Please wait a moment and try again.")
