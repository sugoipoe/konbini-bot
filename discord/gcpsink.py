from discord.ext import voice_recv
from collections import deque
from google.cloud import speech
import asyncio
import time
import wave

"""
There is a GcpSink for each guild_id the bot is in.
"""
class GcpSink(voice_recv.AudioSink):
    def __init__(self, response_coro, guild_id, buffer_size=1024, config=None):
        super().__init__()
        self.buffer_size = buffer_size
        self.buffer = deque(maxlen=self.buffer_size)
        self.config = config or {
            "language_code": "ja-JP",
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "sample_rate_hertz": 48000,
            "audio_channel_count": 2,
            "enable_word_time_offsets": True, # Enable for debugging
        }
        self.response_coro = response_coro
        self.guild_id = guild_id

        # Buffer monitoring properties
        self.last_update_time = None
        self.check_interval = 0.1
        self.stable_period = 0.2

    def write(self, member, data):
        self.buffer.append(data.pcm)

        print(f"{len(self.buffer)}")
        self.last_update_time = time.time()

        if len(self.buffer) >= self.buffer_size:
            self.process_buffer()

    async def process_buffer(self):
        audio_buffer = b"".join(self.buffer)
        self.buffer.clear()
        transcription_result = self.transcribe_audio(audio_buffer)
        await self.response_coro(transcription_result, self.guild_id)

    # Used to determine when the user releases the PTT button
    async def monitor_buffer(self):
        while True:
            await asyncio.sleep(self.check_interval)
            if self.last_update_time:
                time_since_last_update = time.time() - self.last_update_time
                if time_since_last_update >= self.stable_period and self.buffer:
                    await self.process_buffer()

    def wants_opus(self) -> bool:
        return False
    
    def cleanup(self):
        pass

    def save_buffer_to_wav(self, audio_buffer, output_filename="debug_audio.wav", channels=2, sample_width=2, frame_rate=48000):
        # Open a new WAV file for writing
        with wave.open(output_filename, 'wb') as wav_file:
            # Set the WAV file parameters
            wav_file.setnchannels(channels)  # Mono or stereo
            wav_file.setsampwidth(sample_width)  # Sample width in bytes
            wav_file.setframerate(frame_rate)  # Frame rate in Hz
            
            # Write the PCM data to the WAV file
            wav_file.writeframes(audio_buffer)

        print(f"Audio saved to {output_filename}")


    def transcribe_audio(self, audio_buffer, config=None):
        """Transcribes audio data in Linear16 format using Google Cloud Speech-to-Text.

        Args:
            audio_buffer (bytes): The audio data to transcribe in Linear16 encoded binary format.
            config (dict, optional): Configuration options for the Google Cloud Speech-to-Text API. 
        """

        print("transcribing audio")
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_buffer)
        recognition_config = speech.RecognitionConfig(**self.config)

        try:
            response = client.recognize(config=recognition_config, audio=audio)

            self.save_buffer_to_wav(audio_buffer)

            if not response.results:
                print("Got no response for transcription attempt")

            for result in response.results:
                alternative = result.alternatives[0]
                print(f"Transcript: {alternative.transcript}")

        except Exception as e:
            print(f"Error transcribing audio: {e}")

        return alternative.transcript
