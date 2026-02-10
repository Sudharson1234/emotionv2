#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv, find_dotenv

print("Python Executable:", sys.executable)
print("Current Working Directory:", os.getcwd())

# Find .env file
env_path = find_dotenv()
print(f"Found .env file at: {env_path}")

# Load it
load_dotenv(env_path)

# Check if GROQ_API_KEY is loaded
api_key = os.getenv('GROQ_API_KEY')
print(f"GROQ_API_KEY loaded: {api_key[:20]}...{api_key[-10:] if api_key else 'NOT FOUND'}")

if api_key:
    print("\n✓ Environment variables are loading correctly!")
else:
    print("\n✗ ERROR: GROQ_API_KEY not found!")
    print("Make sure .env file is in the project root directory")
