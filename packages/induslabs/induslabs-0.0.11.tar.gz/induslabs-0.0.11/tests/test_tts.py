"""
Unit tests for TTS and Voice functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from induslabs import Client, TTSResponse, TTSStreamResponse, VoiceResponse, Voice


@pytest.fixture
def client():
    """Create a test client"""
    return Client(api_key="test_key")


@pytest.fixture
def mock_tts_response():
    """Create a mock TTS response"""
    mock_response = Mock()
    mock_response.content = b"fake_audio_data"
    mock_response.headers = {
        "x-request-id": "test-123",
        "x-sample-rate": "24000",
        "x-channels": "1",
        "x-bit-depth": "16",
        "x-format": "wav",
    }
    mock_response.raise_for_status = Mock()
    return mock_response


@pytest.fixture
def mock_voices_response():
    """Create a mock voices API response"""
    return {
        "status_code": 200,
        "message": "Voices fetched successfully",
        "error": None,
        "data": {
            "hindi": [
                {"name": "Maya", "voice_id": "Indus-hi-maya", "gender": "female"},
                {"name": "Urvashi", "voice_id": "Indus-hi-Urvashi", "gender": "female"},
            ],
            "english": [
                {"name": "Maya", "voice_id": "Indus-en-maya", "gender": "female"},
                {"name": "Urvashi", "voice_id": "Indus-en-Urvashi", "gender": "female"},
            ],
        },
    }


class TestTTSBasic:
    """Test basic TTS functionality"""

    @patch("requests.post")
    def test_basic_tts(self, mock_post, client, mock_tts_response):
        """Test basic TTS request"""
        mock_post.return_value = mock_tts_response

        response = client.tts.speak(text="Test text", voice="urvashi")

        assert isinstance(response, TTSResponse)
        assert response.content == b"fake_audio_data"
        assert response.request_id == "test-123"
        assert response.sample_rate == 24000
        assert response.channels == 1
        assert response.bit_depth == 16

        # Verify API call
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["text"] == "Test text"
        assert call_kwargs["json"]["voice"] == "urvashi"
        assert call_kwargs["json"]["normalize"] == True

    @patch("requests.post")
    def test_tts_with_language(self, mock_post, client, mock_tts_response):
        """Test TTS with language parameter"""
        mock_post.return_value = mock_tts_response

        response = client.tts.speak(text="Test", voice="urvashi", language="hi-IN")

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["language"] == "hi-IN"

    @patch("requests.post")
    def test_tts_output_formats(self, mock_post, client, mock_tts_response):
        """Test different output formats"""
        mock_post.return_value = mock_tts_response

        for format in ["wav", "mp3", "pcm"]:
            response = client.tts.speak(text="Test", voice="urvashi", output_format=format)

            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["output_format"] == format

    def test_invalid_format(self, client):
        """Test that invalid format raises error"""
        with pytest.raises(ValueError, match="output_format must be"):
            client.tts.speak(text="Test", voice="urvashi", output_format="invalid")

    @patch("requests.post")
    def test_tts_streaming(self, mock_post, client):
        """Test streaming TTS"""
        mock_stream_response = Mock()
        mock_stream_response.headers = {
            "x-request-id": "test-456",
            "x-sample-rate": "24000",
            "x-channels": "1",
            "x-bit-depth": "16",
            "x-format": "wav",
        }
        mock_stream_response.iter_content = Mock(return_value=[b"chunk1", b"chunk2", b"chunk3"])
        mock_stream_response.raise_for_status = Mock()
        mock_post.return_value = mock_stream_response

        response = client.tts.speak(text="Test", voice="urvashi", stream=True)

        assert isinstance(response, TTSStreamResponse)
        assert response.request_id == "test-456"

        # Test iteration
        chunks = list(response.iter_bytes())
        assert len(chunks) == 3
        assert chunks[0] == b"chunk1"

    @patch("requests.post")
    def test_tts_with_temperature(self, mock_post, client, mock_tts_response):
        """Test TTS with temperature parameter"""
        mock_post.return_value = mock_tts_response

        response = client.tts.speak(text="Test", voice="urvashi", temperature=0.8)

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["temperature"] == 0.8

    @patch("requests.post")
    def test_tts_with_max_tokens(self, mock_post, client, mock_tts_response):
        """Test TTS with max_tokens parameter"""
        mock_post.return_value = mock_tts_response

        response = client.tts.speak(text="Test", voice="urvashi", max_tokens=1000)

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["max_tokens"] == 1000


class TestTTSResponse:
    """Test TTSResponse object"""

    def test_response_properties(self):
        """Test response properties"""
        headers = {
            "x-request-id": "test-789",
            "x-sample-rate": "24000",
            "x-channels": "1",
            "x-bit-depth": "16",
            "x-format": "wav",
        }
        response = TTSResponse(b"audio_data", headers, "test-789")

        assert response.sample_rate == 24000
        assert response.channels == 1
        assert response.bit_depth == 16
        assert response.format == "wav"
        assert response.request_id == "test-789"

    def test_get_audio_data(self):
        """Test getting audio data"""
        response = TTSResponse(b"test_audio", {}, "test-id")
        assert response.get_audio_data() == b"test_audio"

    def test_to_file_object(self):
        """Test converting to file object"""
        response = TTSResponse(b"test_audio", {}, "test-id")
        file_obj = response.to_file_object()

        assert file_obj.read() == b"test_audio"
        assert file_obj.seekable()

    @patch("builtins.open", create=True)
    def test_save(self, mock_open):
        """Test saving to file"""
        response = TTSResponse(b"test_audio", {}, "test-id")

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        response.save("test.wav")

        mock_open.assert_called_once_with("test.wav", "wb")
        mock_file.write.assert_called_once_with(b"test_audio")


class TestTTSAsync:
    """Test async TTS functionality"""

    @pytest.mark.asyncio
    async def test_async_tts(self, client):
        """Test async TTS"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = MagicMock()
            mock_response.headers = {
                "x-request-id": "async-123",
                "x-sample-rate": "24000",
                "x-channels": "1",
                "x-bit-depth": "16",
                "x-format": "wav",
            }

            async def mock_read():
                return b"async_audio"

            mock_response.read = mock_read
            mock_response.raise_for_status = Mock()

            mock_post.return_value.__aenter__.return_value = mock_response

            response = await client.tts.speak_async(text="Async test", voice="urvashi")

            assert isinstance(response, TTSResponse)
            assert response.content == b"async_audio"

            await client.close()


class TestVoice:
    """Test Voice object"""

    def test_voice_creation(self):
        """Test creating a Voice object"""
        voice = Voice(name="Maya", voice_id="Indus-hi-maya", gender="female", language="hindi")

        assert voice.name == "Maya"
        assert voice.voice_id == "Indus-hi-maya"
        assert voice.gender == "female"
        assert voice.language == "hindi"

    def test_voice_to_dict(self):
        """Test Voice to_dict method"""
        voice = Voice(name="Maya", voice_id="Indus-hi-maya", gender="female", language="hindi")

        voice_dict = voice.to_dict()
        assert voice_dict == {
            "name": "Maya",
            "voice_id": "Indus-hi-maya",
            "gender": "female",
            "language": "hindi",
        }

    def test_voice_repr(self):
        """Test Voice string representation"""
        voice = Voice(name="Maya", voice_id="Indus-hi-maya", gender="female", language="hindi")

        repr_str = repr(voice)
        assert "Maya" in repr_str
        assert "Indus-hi-maya" in repr_str
        assert "female" in repr_str
        assert "hindi" in repr_str


class TestVoiceResponse:
    """Test VoiceResponse object"""

    def test_voice_response_creation(self, mock_voices_response):
        """Test creating VoiceResponse"""
        response = VoiceResponse(mock_voices_response)

        assert response.status_code == 200
        assert response.message == "Voices fetched successfully"
        assert response.error is None
        assert len(response.voices) == 4  # 2 hindi + 2 english

    def test_voice_response_parsing(self, mock_voices_response):
        """Test voice parsing in VoiceResponse"""
        response = VoiceResponse(mock_voices_response)

        # Check first voice
        first_voice = response.voices[0]
        assert isinstance(first_voice, Voice)
        assert first_voice.name == "Maya"
        assert first_voice.voice_id == "Indus-hi-maya"
        assert first_voice.gender == "female"
        assert first_voice.language == "hindi"

    def test_get_voices_by_language(self, mock_voices_response):
        """Test filtering voices by language"""
        response = VoiceResponse(mock_voices_response)

        hindi_voices = response.get_voices_by_language("hindi")
        assert len(hindi_voices) == 2
        assert all(v.language == "hindi" for v in hindi_voices)

        english_voices = response.get_voices_by_language("english")
        assert len(english_voices) == 2
        assert all(v.language == "english" for v in english_voices)

    def test_get_voices_by_gender(self, mock_voices_response):
        """Test filtering voices by gender"""
        response = VoiceResponse(mock_voices_response)

        female_voices = response.get_voices_by_gender("female")
        assert len(female_voices) == 4
        assert all(v.gender == "female" for v in female_voices)

    def test_get_voice_by_id(self, mock_voices_response):
        """Test getting voice by ID"""
        response = VoiceResponse(mock_voices_response)

        voice = response.get_voice_by_id("Indus-hi-maya")
        assert voice is not None
        assert voice.name == "Maya"
        assert voice.language == "hindi"

        # Test non-existent voice
        voice = response.get_voice_by_id("non-existent")
        assert voice is None

    def test_list_voice_ids(self, mock_voices_response):
        """Test listing all voice IDs"""
        response = VoiceResponse(mock_voices_response)

        voice_ids = response.list_voice_ids()
        assert len(voice_ids) == 4
        assert "Indus-hi-maya" in voice_ids
        assert "Indus-hi-Urvashi" in voice_ids
        assert "Indus-en-maya" in voice_ids
        assert "Indus-en-Urvashi" in voice_ids

    def test_voice_response_to_dict(self, mock_voices_response):
        """Test VoiceResponse to_dict method"""
        response = VoiceResponse(mock_voices_response)

        response_dict = response.to_dict()
        assert response_dict["status_code"] == 200
        assert response_dict["message"] == "Voices fetched successfully"
        assert "data" in response_dict

    def test_voice_response_repr(self, mock_voices_response):
        """Test VoiceResponse string representation"""
        response = VoiceResponse(mock_voices_response)

        repr_str = repr(response)
        assert "VoiceResponse" in repr_str
        assert "4" in repr_str  # number of voices


class TestVoicesAPI:
    """Test Voices API functionality"""

    @patch("requests.post")
    def test_list_voices(self, mock_post, client, mock_voices_response):
        """Test listing voices synchronously"""
        mock_response = Mock()
        mock_response.json.return_value = mock_voices_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        response = client.voices.list()

        assert isinstance(response, VoiceResponse)
        assert len(response.voices) == 4

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "api.indusai.app" in call_args[0][0]
        assert "get-voices" in call_args[0][0]

    @patch("requests.post")
    def test_list_voices_api_error(self, mock_post, client):
        """Test handling API errors when listing voices"""
        mock_post.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            client.voices.list()

    @pytest.mark.asyncio
    async def test_list_voices_async(self, client, mock_voices_response):
        """Test listing voices asynchronously"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = MagicMock()

            async def mock_json():
                return mock_voices_response

            mock_response.json = mock_json
            mock_response.raise_for_status = Mock()

            mock_post.return_value.__aenter__.return_value = mock_response

            response = await client.voices.list_async()

            assert isinstance(response, VoiceResponse)
            assert len(response.voices) == 4

            await client.close()


class TestVoicesIntegration:
    """Test integration between voices and TTS"""

    @patch("requests.post")
    def test_use_voice_from_list(self, mock_post, client, mock_voices_response, mock_tts_response):
        """Test using a voice from the voices list in TTS"""
        # First, mock the voices list
        mock_voices_resp = Mock()
        mock_voices_resp.json.return_value = mock_voices_response
        mock_voices_resp.raise_for_status = Mock()

        # Then mock TTS response
        mock_post.side_effect = [mock_voices_resp, mock_tts_response]

        # Get voices
        voices_response = client.voices.list()
        hindi_voices = voices_response.get_voices_by_language("hindi")

        # Use first Hindi voice for TTS
        tts_response = client.tts.speak(text="Test", voice=hindi_voices[0].voice_id)

        assert isinstance(tts_response, TTSResponse)

        # Verify TTS was called with correct voice_id
        tts_call_kwargs = mock_post.call_args_list[1][1]
        assert tts_call_kwargs["json"]["voice"] == "Indus-hi-maya"


class TestClientInitialization:
    """Test Client initialization and configuration"""

    def test_client_with_custom_urls(self):
        """Test client with custom base URLs"""
        client = Client(
            api_key="test_key",
            base_url="https://custom-tts.example.com",
            voices_base_url="https://custom-voices.example.com",
        )

        assert client.base_url == "https://custom-tts.example.com"
        assert client.voices_base_url == "https://custom-voices.example.com"

    @patch.dict("os.environ", {}, clear=True)
    def test_client_requires_api_key(self):
        """Test that client requires API key"""
        with pytest.raises(ValueError, match="API key must be provided"):
            Client()

    @patch.dict("os.environ", {"INDUSLABS_API_KEY": "env_key"})
    def test_client_from_env(self):
        """Test client initialization from environment variable"""
        client = Client()
        assert client.api_key == "env_key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
