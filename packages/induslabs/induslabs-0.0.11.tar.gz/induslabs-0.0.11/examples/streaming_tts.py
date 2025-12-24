"""
Streaming Text-to-Speech Example
Demonstrates how to receive and process audio as it's generated
"""

import os
from induslabs import Client


def main():
    client = Client()

    # Long text for streaming
    long_text = """
    देखो, मैं यह कहना चाहती हूँ कि ज़िंदगी चाहे कितनी भी मुश्किल क्यों न लगे, 
    अगर हम धैर्य बनाए रखें, अपने काम पर ध्यान दें और दूसरों की भावनाओं को 
    समझने की कोशिश करें, तो हमें न सिर्फ़ अपनी मंज़िल पाने की ताक़त मिलती है 
    बल्कि रास्ते में जो लोग हमारे साथ चलते हैं, उनके दिलों में भी एक अलग ही 
    जगह बन जाती है।
    """

    print("Starting streaming TTS...")
    print("=" * 50)

    # Enable streaming
    response = client.tts.speak(
        text=long_text, voice="Indus-hi-Urvashi", language="hi-IN", stream=True, output_format="wav"
    )

    print(f"Stream started - Request ID: {response.request_id}")
    print(f"Format: {response.format}")
    print(f"Sample Rate: {response.sample_rate}Hz")
    print("\nReceiving audio chunks...")

    # Process chunks as they arrive
    chunk_count = 0
    total_bytes = 0

    # Save while streaming
    with open("streaming_output.wav", "wb") as f:
        for chunk in response.iter_bytes(chunk_size=8192):
            chunk_count += 1
            total_bytes += len(chunk)

            # Write to file
            f.write(chunk)

            # You could also:
            # - Send to audio player for immediate playback
            # - Send over network
            # - Process in real-time

            print(f"Chunk {chunk_count}: {len(chunk)} bytes (Total: {total_bytes} bytes)")

    print("\n" + "=" * 50)
    print(f"Streaming complete!")
    print(f"Total chunks: {chunk_count}")
    print(f"Total bytes: {total_bytes}")
    print(f"Saved to: streaming_output.wav")

    # Alternative: Use the built-in save method for streaming
    print("\n\nAlternative method - direct save from stream:")
    response2 = client.tts.speak(
        text="Another streaming example", voice="Indus-hi-Urvashi", stream=True
    )
    response2.save("streaming_output2.wav")
    print("Saved to: streaming_output2.wav")


if __name__ == "__main__":
    main()
