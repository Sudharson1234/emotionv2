import requests
import time

# Wait for app to start
print("Waiting for app to start...")
time.sleep(5)

try:
    response = requests.get('http://localhost:5000/', timeout=5)
    if response.status_code == 200:
        print("✅ App is running successfully!")
        print(f"   URL: http://127.0.0.1:5000")
        print(f"   Status: {response.status_code}")
    else:
        print(f"⚠️  App returned: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to app")
except Exception as e:
    print(f"❌ Error: {str(e)}")
