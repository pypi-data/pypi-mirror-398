"""
Basic Text-to-Speech Example
"""

import os
from induslabs import Client


def main():
    # Initialize client
    # Make sure to set INDUSLABS_API_KEY environment variable
    # or pass api_key directly: Client(api_key="your_key")
    client = Client()

    # Simple TTS - Hindi
    print("Generating Hindi speech...")
    response = client.tts.speak(
        text="नमस्ते, यह एक टेस्ट है। कैसे हैं आप?", voice="Indus-hi-Urvashi", language="hi-IN"
    )
    response.save("output_hindi.wav")
    print(f"Saved to output_hindi.wav")
    print(f"Sample Rate: {response.sample_rate}Hz")
    print(f"Request ID: {response.request_id}")

    # TTS with different format - MP3
    print("\nGenerating MP3 audio...")
    response = client.tts.speak(
        text="This is a test in English and receiving the data in mp3 format.", voice="Indus-hi-Urvashi", output_format="mp3", sample_rate=24000
    )
    response.save("output_english.wav")
    print(f"Saved to output_english.wav")

    # Working with audio bytes directly
    print("\nWorking with audio in memory...")
    response = client.tts.speak(text="Audio in memory example", voice="Indus-hi-Urvashi")
    audio_bytes = response.get_audio_data()
    print(f"Audio size: {len(audio_bytes)} bytes")

    # Get as file-like object
    audio_file = response.to_file_object()
    print(f"File object seekable: {audio_file.seekable()}")

    print("\nDone!")


if __name__ == "__main__":
    main()
