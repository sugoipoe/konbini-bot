import requests

def convert_to_audio(message: str, speaker: int = 1):
    # First API call - Generate the query JSON blob from the input message
    query_url = 'http://100.97.70.91:50020/audio_query'
    query_params = {
        'text': message,
        'speaker': speaker
    }
    headers = {'accept': 'application/json'}
    response = requests.post(query_url, params=query_params, headers=headers)
    
    if response.status_code != 200:
        print("Failed to generate query from text.")
        return

    query_json = response.json()
    query_json["intonationScale"] = 1.8
    query_json["speedScale"] = 1.3

    # Second API call - Convert the JSON blob to audio using the synthesis endpoint
    synthesis_url = 'http://100.97.70.91:50020/synthesis?speaker=2&enable_interrogative_upspeak=true'
    headers = {
        'accept': 'audio/wav',
        'Content-Type': 'application/json'
    }
    response = requests.post(synthesis_url, json=query_json, headers=headers)
    
    if response.status_code != 200:
        print("Failed to convert text to audio.")
        return

    # Save the returned audio to a file
    with open('audio.wav', 'wb') as audio_file:
        audio_file.write(response.content)
    print("Audio file has been saved as audio.wav.")
