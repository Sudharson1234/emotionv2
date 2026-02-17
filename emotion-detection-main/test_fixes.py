#!/usr/bin/env python3
"""
Test script to verify all fixes are working properly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

def test_endpoints():
    print("=" * 50)
    print("TESTING FIXED ENDPOINTS")
    print("=" * 50)
    
    # Test 1: Check if global chat endpoint returns proper JSON
    print("\n[TEST 1] Global Chat Message Posting")
    print("-" * 50)
    try:
        payload = {
            "message": "Hello from test!",
            "face_emotion": "joy",
            "face_confidence": 0.95
        }
        response = requests.post(f"{BASE_URL}/api/send-global-chat", 
                               json=payload,
                               cookies={'user_id': 'test_user'})
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Type: {type(response.json())}")
        
        # Check if response is JSON (not HTML)
        if "<!doctype" in response.text.lower() or "<!DOCTYPE" in response.text:
            print("❌ FAILED: Got HTML response instead of JSON")
        else:
            try:
                data = response.json()
                if "message_id" in data or "error" in data:
                    print("✅ PASSED: Got proper JSON response")
                    print(f"Response: {json.dumps(data, indent=2, default=str)}")
                else:
                    print("⚠️  WARNING: Response is JSON but missing expected fields")
                    print(f"Response: {json.dumps(data, indent=2, default=str)}")
            except Exception as e:
                print(f"❌ FAILED: Could not parse JSON: {e}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 2: Check global chat users endpoint
    print("\n[TEST 2] Global Chat Users Endpoint")
    print("-" * 50)
    try:
        response = requests.get(f"{BASE_URL}/api/global-chat-users")
        print(f"Status Code: {response.status_code}")
        
        if "<!doctype" in response.text.lower():
            print("❌ FAILED: Got HTML response instead of JSON")
        else:
            try:
                data = response.json()
                print("✅ PASSED: Got proper JSON response")
                print(f"Response: {json.dumps(data, indent=2, default=str)}")
            except Exception as e:
                print(f"❌ FAILED: Could not parse JSON: {e}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 3: Check global chat history
    print("\n[TEST 3] Global Chat History Endpoint")
    print("-" * 50)
    try:
        response = requests.get(f"{BASE_URL}/api/global-chat-history")
        print(f"Status Code: {response.status_code}")
        
        if "<!doctype" in response.text.lower():
            print("❌ FAILED: Got HTML response instead of JSON")
        else:
            try:
                data = response.json()
                print("✅ PASSED: Got proper JSON response")
                message_count = len(data.get('messages', []))
                print(f"Messages in history: {message_count}")
            except Exception as e:
                print(f"❌ FAILED: Could not parse JSON: {e}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 4: Check text detection
    print("\n[TEST 4] Text Emotion Detection Endpoint")
    print("-" * 50)
    try:
        payload = {"text": "I am very happy today!"}
        response = requests.post(f"{BASE_URL}/detect_text_emotion", 
                               json=payload)
        print(f"Status Code: {response.status_code}")
        
        if "<!doctype" in response.text.lower():
            print("❌ FAILED: Got HTML response instead of JSON")
        else:
            try:
                data = response.json()
                print("✅ PASSED: Got proper JSON response")
                print(f"Response: {json.dumps(data, indent=2, default=str)}")
            except Exception as e:
                print(f"❌ FAILED: Could not parse JSON: {e}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 5: Check history endpoints exist
    print("\n[TEST 5] Detection History Endpoints")
    print("-" * 50)
    endpoints = [
        "/get_text_detection_history",
        "/get_image_detection_history",
        "/get_video_detection_history"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"\n{endpoint}:")
            print(f"  Status Code: {response.status_code}")
            
            if "<!doctype" in response.text.lower():
                print(f"  ❌ Got HTML response instead of JSON")
            else:
                try:
                    data = response.json()
                    print(f"  ✅ Got proper JSON response")
                    print(f"  Response type: {type(data)}")
                except Exception as e:
                    print(f"  Could not parse JSON: {e}")
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 50)
    print("TESTS COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    print("Make sure the app is running on http://127.0.0.1:5000")
    print("Starting tests...\n")
    test_endpoints()
