"""
Voice Listing and Selection Example
"""

import os
from induslabs import Client


def main():
    # Initialize client
    # Make sure to set INDUSLABS_API_KEY environment variable
    # or pass api_key directly: Client(api_key="your_key")
    client = Client()

    # List all available voices
    print("Fetching all available voices...")
    voices_response = client.voices.list()
    print(f"Status: {voices_response.message}")
    print(f"Total voices available: {len(voices_response.voices)}\n")

    # Display all voices
    print("=" * 60)
    print("All Available Voices:")
    print("=" * 60)
    for voice in voices_response.voices:
        print(f"  Name: {voice.name}")
        print(f"  Voice ID: {voice.voice_id}")
        print(f"  Language: {voice.language}")
        print(f"  Gender: {voice.gender}")
        print("-" * 60)

    # Get voices by language
    print("\nHindi Voices:")
    print("=" * 60)
    hindi_voices = voices_response.get_voices_by_language("hindi")
    for voice in hindi_voices:
        print(f"  {voice.name} ({voice.voice_id}) - {voice.gender}")

    print("\nEnglish Voices:")
    print("=" * 60)
    english_voices = voices_response.get_voices_by_language("english")
    for voice in english_voices:
        print(f"  {voice.name} ({voice.voice_id}) - {voice.gender}")

    # Get voices by gender
    print("\nFemale Voices:")
    print("=" * 60)
    female_voices = voices_response.get_voices_by_gender("female")
    for voice in female_voices:
        print(f"  {voice.name} ({voice.voice_id}) - {voice.language}")

    # Get specific voice by ID
    print("\nLooking up specific voice...")
    print("=" * 60)
    specific_voice = voices_response.get_voice_by_id("Indus-hi-maya")
    if specific_voice:
        print(f"  Found: {specific_voice.name}")
        print(f"  Language: {specific_voice.language}")
        print(f"  Gender: {specific_voice.gender}")

    # List all voice IDs (useful for quick reference)
    print("\nAll Voice IDs:")
    print("=" * 60)
    voice_ids = voices_response.list_voice_ids()
    for voice_id in voice_ids:
        print(f"  - {voice_id}")

    # Use a voice from the list for TTS
    print("\nUsing a voice for text-to-speech...")
    print("=" * 60)
    if hindi_voices:
        selected_voice = hindi_voices[0]
        print(f"Selected voice: {selected_voice.name} ({selected_voice.voice_id})")

        tts_response = client.tts.speak(
            text=f"नमस्ते! मैं {selected_voice.name} हूं।",
            voice=selected_voice.voice_id,
            language="hi-IN",
        )
        tts_response.save(f"output_{selected_voice.name.lower()}.wav")
        print(f"Audio saved to output_{selected_voice.name.lower()}.wav")

    # Export voice data
    print("\nExporting voice data...")
    print("=" * 60)
    voice_data = voices_response.to_dict()
    print(f"Exported {len(voice_data['data'])} language groups")

    # Convert a voice to dictionary
    if voices_response.voices:
        sample_voice = voices_response.voices[0]
        voice_dict = sample_voice.to_dict()
        print(f"\nSample voice data: {voice_dict}")

    print("\nDone!")


if __name__ == "__main__":
    main()
