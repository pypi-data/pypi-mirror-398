"""
Universal Streaming Text-to-Speech Player

This example demonstrates how to stream audio from the IndusLabs TTS API
and play it in real-time with support for WAV, MP3, and PCM formats.

Requirements:
    pip install induslabs pyaudio pydub

System Dependencies:
    - Ubuntu/Debian: sudo apt-get install portaudio19-dev python3-pyaudio ffmpeg
    - macOS: brew install portaudio ffmpeg
    - Windows: Install PyAudio wheel from PyPI and ffmpeg from https://ffmpeg.org/

How Streaming Works:
--------------------
1. Audio chunks are received from the API in real-time
2. For MP3: Chunks are decoded to raw PCM using pydub/ffmpeg
3. For WAV: After the header, raw PCM data is extracted
4. For PCM: Raw data is used directly
5. Decoded audio is queued and played through PyAudio
6. Simultaneous playback and file saving occurs

Integration Guide:
-----------------
This player can be integrated into:
- Voice assistants and chatbots
- Interactive kiosks and displays
- Telephony systems (modify for appropriate sample rate)
- Real-time translation apps
- Accessibility tools
- Gaming and entertainment applications

For web applications, consider using WebSockets to stream audio to browser.
For mobile apps, use platform-specific audio APIs (AVAudioEngine on iOS, AudioTrack on Android).
"""

import queue
import threading
import time
import pyaudio
from io import BytesIO
from pydub import AudioSegment
from induslabs import Client


class UniversalStreamingTTSPlayer:
    """
    Handles real-time streaming playback of TTS audio with support for multiple formats.
    
    Supports:
    - WAV: Uncompressed audio (fastest, no decoding needed)
    - MP3: Compressed audio (smaller bandwidth, requires decoding)
    - PCM: Raw audio data (no container, direct playback)
    
    Architecture:
    - Producer thread: Receives and decodes audio chunks from API
    - Consumer thread: Plays decoded audio from queue
    - Main thread: Coordinates and manages lifecycle
    """

    def __init__(self, sample_rate=24000, channels=1, chunk_size=4096):
        """
        Initialize the streaming player.
        
        Args:
            sample_rate: Audio sample rate in Hz (default: 24000)
            channels: Number of audio channels (1=mono, 2=stereo)
            chunk_size: Size of audio chunks for streaming (bytes)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.streaming_complete = False
        self.playing = False
        
        # Audio format detection
        self.format_detected = None
        self.wav_header_skipped = False
        self.mp3_buffer = BytesIO()

        self.p = pyaudio.PyAudio()
        self.stream = None

    def _detect_format(self, first_chunk: bytes) -> str:
        """
        Detect audio format from the first chunk.
        
        Args:
            first_chunk: Initial bytes of audio data
            
        Returns:
            Format string: 'wav', 'mp3', or 'pcm'
        """
        if first_chunk.startswith(b'RIFF'):
            return 'wav'
        elif first_chunk.startswith(b'ID3') or first_chunk.startswith(b'\xff\xfb') or first_chunk.startswith(b'\xff\xf3'):
            return 'mp3'
        else:
            return 'pcm'

    def _decode_mp3_chunk(self, chunk: bytes) -> bytes:
        """
        Decode MP3 chunk to raw PCM data.
        
        MP3 decoding requires complete frames. This method buffers data
        and decodes when possible, handling partial frames gracefully.
        
        Args:
            chunk: Raw MP3 data
            
        Returns:
            Decoded PCM audio data
        """
        self.mp3_buffer.write(chunk)
        
        # Try to decode accumulated data
        self.mp3_buffer.seek(0)
        try:
            audio = AudioSegment.from_mp3(self.mp3_buffer)
            # Convert to raw PCM data matching our output format
            pcm_data = audio.set_frame_rate(self.sample_rate).set_channels(self.channels).raw_data
            
            # Clear buffer after successful decode
            self.mp3_buffer = BytesIO()
            return pcm_data
        except Exception:
            # Not enough data yet for complete frame, continue buffering
            return b''

    def _process_wav_chunk(self, chunk: bytes) -> bytes:
        """
        Process WAV chunk by skipping header and extracting PCM data.
        
        WAV files have a 44-byte header followed by raw PCM data.
        This method skips the header on first chunk only.
        
        Args:
            chunk: Raw WAV data
            
        Returns:
            Raw PCM audio data
        """
        if not self.wav_header_skipped:
            # Skip WAV header (typically 44 bytes)
            if len(chunk) > 44:
                self.wav_header_skipped = True
                return chunk[44:]
            return b''
        return chunk

    def _stream_audio(self, response, save_path=None, output_format='wav'):
        """
        Receives audio chunks from API, decodes, and queues for playback.
        
        This runs in a separate thread (producer) and handles:
        - Format detection
        - Format-specific decoding
        - File saving (original format)
        - Queueing decoded audio for playback
        
        Args:
            response: Streaming response from client.tts.speak()
            save_path: Optional path to save audio file
            output_format: Format of the streaming audio ('wav', 'mp3', 'pcm')
        """
        file_handle = open(save_path, "wb") if save_path else None
        first_chunk = True

        try:
            for chunk in response.iter_bytes(chunk_size=self.chunk_size):
                # Save original chunk to file
                if file_handle:
                    file_handle.write(chunk)
                
                # Detect format from first chunk
                if first_chunk:
                    self.format_detected = self._detect_format(chunk) if output_format == 'wav' else output_format
                    print(f"Format detected: {self.format_detected}")
                    first_chunk = False
                
                # Decode based on format
                if self.format_detected == 'mp3':
                    decoded_chunk = self._decode_mp3_chunk(chunk)
                elif self.format_detected == 'wav':
                    decoded_chunk = self._process_wav_chunk(chunk)
                else:  # pcm
                    decoded_chunk = chunk
                
                # Queue decoded audio for playback
                if decoded_chunk:
                    self.audio_queue.put(decoded_chunk)
                    
        finally:
            # Flush any remaining MP3 data
            if self.format_detected == 'mp3' and self.mp3_buffer.tell() > 0:
                try:
                    self.mp3_buffer.seek(0)
                    audio = AudioSegment.from_mp3(self.mp3_buffer)
                    final_pcm = audio.set_frame_rate(self.sample_rate).set_channels(self.channels).raw_data
                    if final_pcm:
                        self.audio_queue.put(final_pcm)
                except Exception:
                    pass
            
            self.streaming_complete = True
            if file_handle:
                file_handle.close()

    def _play_audio(self):
        """
        Plays audio chunks from the queue (consumer thread).
        
        This runs in a separate thread and continuously:
        - Dequeues decoded PCM audio
        - Writes to PyAudio stream for playback
        - Handles queue timeouts gracefully
        """
        while self.playing:
            try:
                chunk = self.audio_queue.get(timeout=0.05)
                if chunk is None:
                    break
                self.stream.write(chunk)
            except queue.Empty:
                if self.streaming_complete:
                    break

    def play(self, response, save_path=None, output_format='wav', prebuffer_seconds=1.0):
        """
        Stream and play TTS audio in real-time with support for all formats.
        
        This is the main entry point that orchestrates:
        1. Opening audio output stream
        2. Starting producer thread (receiving/decoding)
        3. Buffering initial audio for smooth playback
        4. Starting consumer thread (playback)
        5. Waiting for completion and cleanup
        
        Args:
            response: Streaming response from client.tts.speak()
            save_path: Optional path to save audio file (in original format)
            output_format: Format of the streaming audio ('wav', 'mp3', 'pcm')
            prebuffer_seconds: Seconds of audio to buffer before playback starts
                             (reduces stuttering, increases latency)
        
        Example:
            >>> player = UniversalStreamingTTSPlayer()
            >>> response = client.tts.speak(text="Hello", stream=True, output_format="mp3")
            >>> player.play(response, save_path="output.mp3", output_format="mp3")
        """
        # Open audio output stream
        self.stream = self.p.open(
            format=pyaudio.paInt16,  # 16-bit PCM
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.chunk_size,
        )

        self.playing = True
        self.streaming_complete = False
        self.wav_header_skipped = False
        self.mp3_buffer = BytesIO()

        # Start streaming thread (producer)
        stream_thread = threading.Thread(
            target=self._stream_audio, 
            args=(response, save_path, output_format), 
            daemon=True
        )
        stream_thread.start()

        # Wait for initial buffer
        chunks_needed = int(
            (self.sample_rate * self.channels * 2 / self.chunk_size) * prebuffer_seconds
        )
        print(f"Buffering {prebuffer_seconds}s of audio...")

        start_time = time.time()
        while self.audio_queue.qsize() < chunks_needed:
            if self.streaming_complete:
                break
            if time.time() - start_time > 10:  # Timeout after 10 seconds
                print("Buffering timeout, starting playback with available data...")
                break
            time.sleep(0.1)

        print("Playing audio...\n")

        # Start playback thread (consumer)
        play_thread = threading.Thread(target=self._play_audio, daemon=True)
        play_thread.start()

        # Wait for completion
        stream_thread.join()
        play_thread.join()

        # Cleanup
        self.stream.stop_stream()
        self.stream.close()

    def close(self):
        """Release audio resources."""
        self.p.terminate()


def main():
    """
    Demonstration of streaming TTS with multiple formats.
    
    This example shows how to use the player with WAV, MP3, and PCM formats.
    Choose the format based on your needs:
    - WAV: Best quality, largest size, no decoding overhead
    - MP3: Good quality, smaller size, requires decoding
    - PCM: Raw data, minimal overhead, no container format
    """
    # Initialize the client
    client = Client()  # Uses INDUSLABS_API_KEY environment variable

    # Text to convert to speech
    text = """
    The history of artificial intelligence spans several decades, beginning in the 1950s when 
    pioneers like Alan Turing first proposed the idea that machines could think. The Turing Test, 
    introduced in 1950, became a foundational concept for evaluating machine intelligence.
    """

    print("=" * 70)
    print("IndusLabs Universal Streaming TTS Example")
    print("=" * 70)

    # Test with different formats
    formats_to_test = [
        ("wav", "output.wav"),
        ("mp3", "output.mp3"),
        ("pcm", "output.pcm")
    ]

    for output_format, save_path in formats_to_test:
        print(f"\n{'='*70}")
        print(f"Testing format: {output_format.upper()}")
        print(f"{'='*70}\n")

        # Create streaming response
        response = client.tts.speak(
            text=text,
            voice="Indus-hi-Urvashi",
            output_format=output_format,
            stream=True
        )

        # Create player and play audio
        player = UniversalStreamingTTSPlayer()

        try:
            player.play(
                response, 
                save_path=save_path, 
                output_format=output_format,
                prebuffer_seconds=1.0
            )
            print(f"✓ Playback complete!")
            print(f"✓ Audio saved to: {save_path}\n")
        except Exception as e:
            print(f"✗ Error with {output_format}: {e}\n")
        finally:
            player.close()

    print("=" * 70)
    print("All formats tested successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()