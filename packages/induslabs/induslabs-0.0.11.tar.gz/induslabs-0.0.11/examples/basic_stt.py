"""
Basic Speech-to-Text Example
"""

import os
from induslabs import Client


def main():
    client = Client()

    # Example 1: Transcribe from file path
    print("Example 1: Transcribing from file...")
    print("=" * 50)

    # Make sure you have an audio file to test
    audio_file = "test_audio.wav"

    if os.path.exists(audio_file):
        result = client.stt.transcribe(file=audio_file)

        print(f"Transcription: {result.text}")
        print(f"\nDetailed Information:")
        print(f"  Request ID: {result.request_id}")
        print(f"  Language Detected: {result.language_detected}")
        audio_duration = (
            f"{result.audio_duration_seconds:.2f}s"
            if result.audio_duration_seconds is not None
            else "N/A"
        )
        processing_time = (
            f"{result.processing_time_seconds:.2f}s"
            if result.processing_time_seconds is not None
            else "N/A"
        )
        first_token_time = (
            f"{result.first_token_time_seconds:.4f}s"
            if result.first_token_time_seconds is not None
            else "N/A"
        )
        credits_used = result.credits_used if result.credits_used is not None else "N/A"

        print(f"  Audio Duration: {audio_duration}")
        print(f"  Processing Time: {processing_time}")
        print(f"  First Token Time: {first_token_time}")
        print(f"  Credits Used: {credits_used}")
    else:
        print(f"Audio file '{audio_file}' not found.")
        print("Creating a sample audio file using TTS...")

        # Create sample audio
        tts_response = client.tts.speak(
            text="यह एक टेस्ट है। भाषण से पाठ रूपांतरण का परीक्षण।",
            voice="Indus-hi-Urvashi",
        )
        tts_response.save(audio_file)
        print(f"Created {audio_file}")

        # Now transcribe
        result = client.stt.transcribe(file=audio_file)
        print(f"\nTranscription: {result.text}")

    # Example 2: Transcribe from file object
    print("\n\nExample 2: Transcribing from file object...")
    print("=" * 50)

    if os.path.exists(audio_file):
        with open(audio_file, "rb") as f:
            result = client.stt.transcribe(file=f)
            print(f"Transcription: {result.text}")

    # Example 3: Using the result object
    print("\n\nExample 3: Working with result object...")
    print("=" * 50)

    if os.path.exists(audio_file):
        result = client.stt.transcribe(audio_file)

        # String representation
        print(f"As string: {str(result)}")

        # Dict representation
        result_dict = result.to_dict()
        print(f"\nAs dictionary:")
        for key, value in result_dict.items():
            print(f"  {key}: {value}")

    # Example 4: Noise cancellation with custom chunk size
    print("\n\nExample 4: Noise cancellation (non-streaming)...")
    print("=" * 50)

    if os.path.exists(audio_file):
        result = client.stt.transcribe(
            file=audio_file,
            chunk_size=16384,
            noise_cancellation=True,
        )
        print(f"Transcription: {result.text}")
        print("  Noise cancellation: Enabled (non-streaming mode)")
        if result.metrics:
            print(f"  RTF: {result.metrics.rtf:.3f}")


if __name__ == "__main__":
    main()
