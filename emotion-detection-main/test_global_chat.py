#!/usr/bin/env python3
"""Test the global chat endpoint"""
import requests
import json
import time

# Test endpoint
base_url = "http://localhost:5000"

# Test 1: Simple text message to global chat
print("=" * 60)
print("TEST 1: Global Chat - Simple message")
print("=" * 60)

test_messages = [
    "hello! how are you?",
    "I'm feeling great today!",
    "¡Hola! ¿Cómo estás?",  # Spanish
    "Bonjour! Comment allez-vous?",  # French
]

for message in test_messages:
    print(f"\n📝 Sending: {message}")
    try:
        response = requests.post(
            f"{base_url}/api/global-chat",
            json={"message": message},
            timeout=15
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"  - Detected Language: {data.get('language_name', 'Unknown')}")
            print(f"  - Emotion: {data.get('emotion', 'Unknown')}")
            print(f"  - AI Response: {data.get('ai_response_text', 'No response')[:100]}...")
        else:
            print(f"❌ Error: {response.text}")
    except requests.exceptions.Timeout:
        print(f"⏱️ TIMEOUT: Request took too long")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    time.sleep(1)

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
