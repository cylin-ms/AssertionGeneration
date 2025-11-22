import requests
import json

def test_ollama_connection():
    base_url = "http://192.168.2.163:11434"
    
    # 1. Test basic connectivity via /api/tags
    print(f"1. Testing basic connectivity to {base_url}/api/tags...")
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Basic connectivity successful!")
            models = response.json().get('models', [])
            print(f"Available models: {[m['name'] for m in models]}")
        else:
            print(f"❌ Basic connectivity failed with status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        return

    # 2. Test generation
    url = f"{base_url}/api/generate"
    model = "gpt-oss:20b"  # Using the model mentioned in previous context
    
    print(f"\n2. Testing generation with model '{model}'...")
    
    payload = {
        "model": model,
        "prompt": "Hello",
        "stream": False
    }
    
    try:
        # Increased timeout to 60s for model loading
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            print("✅ Generation successful!")
            result = response.json()
            print(f"Response: {result.get('response', '').strip()}")
        else:
            print(f"❌ Generation failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {url}")
    except requests.exceptions.Timeout:
        print(f"❌ Timeout error: The request to {url} timed out.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    test_ollama_connection()
