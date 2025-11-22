import requests

try:
    response = requests.get('http://192.168.2.204:11434/api/tags')
    if response.status_code == 200:
        print("Available models:")
        for model in response.json()['models']:
            print(f"- {model['name']}")
    else:
        print(f"Error: Status {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Connection error: {e}")
