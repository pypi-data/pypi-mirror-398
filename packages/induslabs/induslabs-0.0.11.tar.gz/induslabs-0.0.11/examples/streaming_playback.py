"""
Streaming Text-to-Speech Example

This example demonstrates how to stream audio from the IndusLabs TTS API
and play it in real-time while simultaneously saving to a file.

Requirements:
    pip install induslabs pyaudio

Note: PyAudio may require additional system dependencies:
    - Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio
    - macOS: brew install portaudio
    - Windows: PyAudio wheels available on PyPI
"""

import queue
import threading
import time
import pyaudio
from induslabs import Client


class StreamingTTSPlayer:
    """Handles real-time streaming playback of TTS audio with buffering"""

    def __init__(self, sample_rate=24000, channels=1, chunk_size=4096):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.streaming_complete = False
        self.playing = False

        self.p = pyaudio.PyAudio()
        self.stream = None

    def _stream_audio(self, response, save_path=None):
        """Receives audio chunks from API and queues them for playback"""
        file_handle = open(save_path, "wb") if save_path else None

        try:
            for chunk in response.iter_bytes(chunk_size=self.chunk_size):
                self.audio_queue.put(chunk)
                if file_handle:
                    file_handle.write(chunk)
        finally:
            self.streaming_complete = True
            if file_handle:
                file_handle.close()

    def _play_audio(self):
        """Plays audio chunks from the queue"""
        while self.playing:
            try:
                chunk = self.audio_queue.get(timeout=0.05)
                if chunk is None:
                    break
                self.stream.write(chunk)
            except queue.Empty:
                if self.streaming_complete:
                    break

    def play(self, response, save_path=None, prebuffer_seconds=1.0):
        """
        Stream and play TTS audio in real-time

        Args:
            response: Streaming response from client.tts.speak()
            save_path: Optional path to save audio file
            prebuffer_seconds: Seconds of audio to buffer before playback starts
        """
        # Open audio output stream
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.chunk_size,
        )

        self.playing = True
        self.streaming_complete = False

        # Start streaming thread
        stream_thread = threading.Thread(
            target=self._stream_audio, args=(response, save_path), daemon=True
        )
        stream_thread.start()

        # Wait for initial buffer
        chunks_needed = int(
            (self.sample_rate * self.channels * 2 / self.chunk_size) * prebuffer_seconds
        )
        print(f"Buffering {prebuffer_seconds}s of audio...")

        while self.audio_queue.qsize() < chunks_needed:
            if self.streaming_complete:
                break
            time.sleep(0.1)

        print("Playing audio...\n")

        # Start playback thread
        play_thread = threading.Thread(target=self._play_audio, daemon=True)
        play_thread.start()

        # Wait for completion
        stream_thread.join()
        play_thread.join()

        # Cleanup
        self.stream.stop_stream()
        self.stream.close()

    def close(self):
        """Release audio resources"""
        self.p.terminate()


def main():
    # Initialize the client
    client = Client()  # Uses INDUSLABS_API_KEY environment variable

    # Text to convert to speech
    text = """
    The history of artificial intelligence spans several decades, beginning in the 1950s when 
    pioneers like Alan Turing first proposed the idea that machines could think. The Turing Test, 
    introduced in 1950, became a foundational concept for evaluating machine intelligence. In the 
    following years, researchers developed early AI programs that could play games, solve algebra 
    problems, and prove mathematical theorems.

    The 1960s and 1970s saw tremendous optimism about AI's potential. Researchers believed that 
    human-level artificial intelligence was just around the corner. However, this optimism was 
    premature. The limitations of computing power, the complexity of human intelligence, and 
    insufficient understanding of how the brain works led to what became known as the "AI winter" 
    in the 1980s, when funding and interest in AI research declined dramatically.

    The field experienced a resurgence in the 1990s with the advent of machine learning approaches 
    that didn't rely solely on hand-coded rules. Instead, these systems could learn from data. 
    The development of support vector machines, decision trees, and neural networks opened new 
    possibilities. In 1997, IBM's Deep Blue defeated world chess champion Garry Kasparov, marking 
    a significant milestone in AI history.

    The twenty-first century brought exponential growth in AI capabilities. The explosion of 
    available data, combined with massive increases in computational power and algorithmic 
    innovations, created perfect conditions for AI advancement. Deep learning, a subset of machine 
    learning based on artificial neural networks, emerged as a game-changing technology. In 2012, 
    a deep learning system dramatically improved image recognition accuracy, sparking a revolution 
    in computer vision.

    Natural language processing also saw remarkable progress. Systems like GPT, BERT, and their 
    successors demonstrated unprecedented abilities to understand and generate human language. 
    These models, trained on vast amounts of text data, could engage in conversations, write 
    essays, translate languages, and even generate creative content like poetry and stories.

    Today, AI is embedded in countless aspects of our daily lives. Virtual assistants like Siri 
    and Alexa respond to our voice commands. Recommendation systems on Netflix and Spotify suggest 
    content we might enjoy. Autonomous vehicles are being tested on public roads. Medical AI 
    systems help doctors diagnose diseases from medical images with superhuman accuracy. Financial 
    institutions use AI to detect fraud and make trading decisions.
    """

    print("=" * 60)
    print("IndusLabs Streaming TTS Example")
    print("=" * 60)

    # Create streaming response
    response = client.tts.speak(
        text=text, voice="Indus-hi-Urvashi", stream=True  # Enable streaming
    )

    # Create player and play audio
    player = StreamingTTSPlayer()

    try:
        # Play audio in real-time and save to file
        player.play(response, save_path="output.wav", prebuffer_seconds=1.0)
        print("Playback complete!")
        print("Audio saved to: output.wav")
    finally:
        player.close()


if __name__ == "__main__":
    main()
