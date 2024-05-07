import base64
import wave

def save_b64_string_to_wav(b64_string: str, filename: str):
    """
    Converts a base64 encoded string of audio data to a WAV file and saves it.

    Parameters:
        b64_string (str): The base64 encoded string of the audio.
        filename (str): The path where the WAV file will be saved.
    """
    # Decode the base64 string to bytes
    audio_bytes = base64.b64decode(b64_string)
    
    # Open a WAV file for writing
    with wave.open(filename, 'w') as wav_file:
        # Set the parameters needed for the WAV file
        num_channels = 2  # Mono
        sample_width = 2  # 2 bytes per sample because of int16
        frame_rate = 24000  # Samples per second
        
        # Set the WAV file's parameters
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(frame_rate)
        
        # Write the decoded bytes to the WAV file
        wav_file.writeframes(audio_bytes)
        print(f"Saved to {filename}")


def save_hex_to_wav(hex_bytes: bytes, filename: str):
    """
    Converts a hex string of audio data to a WAV file and saves it.

    Parameters:
        hex_string (str): The hex string of the audio.
        filename (str): The path where the WAV file will be saved.
    """
    # Open a WAV file for writing
    with wave.open(filename, 'w') as wav_file:
        # Set the parameters needed for the WAV file
        num_channels = 2  # Mono
        sample_width = 2  # 2 bytes per sample because of int16
        frame_rate = 24000  # Samples per second
        
        # Set the WAV file's parameters
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(frame_rate)
        
        # Write the decoded bytes to the WAV file
        wav_file.writeframes(hex_bytes)
        print(f"Saved to {filename}")

def hex_to_b64(input_hex) -> bytes:
    # Encode the hex bytes to a base64 bytes
    audio_b64 = base64.b64encode(input_hex)
    return audio_b64

def hex_to_b64_string(input_hex) -> str:
    # Encode the hex bytes to a base64 string
    audio_string_b64 = hex_to_b64(input_hex).decode('utf-8')
    return audio_string_b64
    