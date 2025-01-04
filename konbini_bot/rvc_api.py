import requests

# Define the URL and endpoint
query_url = 'http://100.97.70.91:8001'

def change_voice(b64_audio: str) -> str:
    # Define the endpoint
    endpoint = "/change_voice"

    # Define the payload
    payload = {
        "b64_audio": b64_audio
    }

    # Make the API call
    response = requests.post(query_url + endpoint, json=payload)

    # Check the response status code
    if response.status_code == 200:
        # API call was successful
        return response.json()
    else:
        # API call failed
        return None
