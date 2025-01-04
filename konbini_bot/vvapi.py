import requests
import os

BASE_AUDIO_DIR = 'response_logs/'


def write_text_to_wav(message: str, filename: str, speaker: int = 1):
    hex_audio = text_to_hex_audio(message, speaker)

    try:
        with open(filename, 'wb') as audio_file:
            audio_file.write(hex_audio)
    except Exception as e:
        print(e)
        print("Failed to write audio to file.")

    return

def text_to_hex_audio(message: str, speaker: int = 1, sample_rate: int = 48000):  # Rename this
    # Returns a base64 encoded string of the audio generated from the input message
    query_url = 'http://100.97.70.91:50020/audio_query'
    query_params = {
        'text': message,
        'speaker': speaker,
        'outputSamplingRate': sample_rate
    }
    headers = {'accept': 'application/json'}
    try:
        response = requests.post(query_url, params=query_params, headers=headers)
    except Exception as e:
        print(e)
        print("Handle this exception if it happens again. It's probably because the remote API is down.")
        print("It could be down because it's not running, or because nginx isn't running.")
        return
    
    if response.status_code != 200:
        print("Failed to generate query from text.")
        return

    query_json = response.json()
    query_json["intonationScale"] = 1.4
    query_json["speedScale"] = 1.7
    query_json["outputSamplingRate"] = sample_rate

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
    
    return response.content