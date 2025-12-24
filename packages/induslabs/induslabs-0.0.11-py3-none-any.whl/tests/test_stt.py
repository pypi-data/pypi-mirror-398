"""Updated unit tests for the WebSocket-based STT client."""

import json
import warnings
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import aiohttp
import pytest

from induslabs import Client, STTResponse, STTSegment


class MockWS:
    def __init__(self, messages):
        self.messages = messages

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)

    async def send_bytes(self, data):
        pass


@pytest.fixture
def client():
    return Client(api_key="4RzC13dC8ZUasNUwn1yJGi7bI1bwT1_U-t8oCfnSbBc")


@pytest.fixture
def mock_audio_data():
    return b"fake_audio_data_pcm16"


def _ws_messages(final_text="hello world", request_id="req-123"):
    return [
        json.dumps({"type": "chunk_final", "text": "hello", "start": 0.0, "end": 1.0}),
        json.dumps({"type": "final", "text": final_text, "request_id": request_id}),
        json.dumps(
            {
                "type": "metrics",
                "buffer": 2.0,
                "transcription": 0.5,
                "total": 0.6,
                "RTF": 0.3,
                "request_id": request_id,
            }
        ),
    ]


class TestSTTTranscribe:
    @patch("websocket.WebSocket")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_audio")
    def test_non_streaming_with_noise_cancellation(
        self, mock_file, mock_ws_class, client, mock_audio_data
    ):
        mock_ws = MagicMock()
        mock_ws_class.return_value = mock_ws
        mock_ws.recv.side_effect = _ws_messages()

        with patch.object(client.stt, "_convert_audio_to_pcm16", return_value=mock_audio_data):
            result = client.stt.transcribe(
                file="sample.wav",
                model="indus-stt-v1",
                streaming=False,
                noise_cancellation=True,
            )

        assert isinstance(result, STTResponse)
        assert result.text == "hello world"
        assert len(result.segments) == 1
        assert result.segments[0].text == "hello"
        url = mock_ws.connect.call_args[0][0]
        assert "streaming=false" in url
        assert "noise_cancellation=true" in url

    @patch("websocket.WebSocket")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_audio")
    def test_streaming_with_noise_warning_and_callback(
        self, mock_file, mock_ws_class, client, mock_audio_data
    ):
        mock_ws = MagicMock()
        mock_ws_class.return_value = mock_ws
        mock_ws.recv.side_effect = _ws_messages(final_text="streamed", request_id="req-stream")

        captured_segments = []

        def on_segment(segment: STTSegment):
            captured_segments.append(segment.text)

        with patch.object(client.stt, "_convert_audio_to_pcm16", return_value=mock_audio_data):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = client.stt.transcribe(
                    file="sample.wav",
                    model="indus-stt-hi-en",
                    streaming=True,
                    noise_cancellation=True,
                    language="hindi",
                    on_segment=on_segment,
                )

        assert result.text == "streamed"
        assert captured_segments == ["hello"]
        assert any("only supported in non-streaming" in str(w.message) for w in caught)

    @patch("websocket.WebSocket")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_audio")
    def test_transcribe_from_file_object(self, mock_file, mock_ws_class, client, mock_audio_data):
        mock_ws = MagicMock()
        mock_ws_class.return_value = mock_ws
        mock_ws.recv.side_effect = _ws_messages(final_text="object", request_id="req-obj")

        with patch.object(client.stt, "_convert_audio_to_pcm16", return_value=mock_audio_data):
            result = client.stt.transcribe(file=BytesIO(b"test-bytes"))

        assert result.text == "object"
        assert result.request_id == "req-obj"

    @patch("websocket.WebSocket")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_audio")
    def test_server_error_sets_response_error(
        self, mock_file, mock_ws_class, client, mock_audio_data
    ):
        mock_ws = MagicMock()
        mock_ws_class.return_value = mock_ws
        mock_ws.recv.side_effect = [json.dumps({"type": "error", "message": "boom"})]

        with patch.object(client.stt, "_convert_audio_to_pcm16", return_value=mock_audio_data):
            result = client.stt.transcribe("sample.wav")

        assert result.has_error
        assert "boom" in result.error

    @patch("websocket.WebSocket")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_audio")
    def test_connection_failure_sets_error(self, mock_file, mock_ws_class, client):
        mock_ws = MagicMock()
        mock_ws.connect.side_effect = RuntimeError("no network")
        mock_ws_class.return_value = mock_ws

        with patch.object(client.stt, "_convert_audio_to_pcm16", return_value=b"fake_pcm"):
            result = client.stt.transcribe("sample.wav")

        assert result.has_error
        assert "no network" in result.error

    def test_invalid_model_raises(self, client):
        with pytest.raises(ValueError):
            client.stt.transcribe("sample.wav", model="unknown")

    def test_streaming_with_v1_model_raises(self, client):
        with pytest.raises(ValueError):
            client.stt.transcribe("sample.wav", model="indus-stt-v1", streaming=True)


class TestSTTAsync:
    @pytest.mark.asyncio
    async def test_async_non_streaming_with_noise_cancellation(self, client, mock_audio_data):
        messages = [
            SimpleNamespace(type=aiohttp.WSMsgType.TEXT, data=payload)
            for payload in _ws_messages(final_text="async", request_id="req-async")
        ]
        mock_ws = MockWS(messages)

        mock_ws_context = AsyncMock()
        mock_ws_context.__aenter__.return_value = mock_ws

        mock_session = MagicMock()
        mock_session.ws_connect.return_value = mock_ws_context
        mock_session.close = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch("builtins.open", mock_open(read_data=b"fake_audio")):
                with patch.object(
                    client.stt, "_convert_audio_to_pcm16", return_value=mock_audio_data
                ):
                    result = await client.stt.transcribe_async(
                        "sample.wav", streaming=False, noise_cancellation=True
                    )

        assert result.text == "async"
        mock_session.ws_connect.assert_called_once()
        await client.stt.close()

    @pytest.mark.asyncio
    async def test_async_streaming_warning(self, client, mock_audio_data):
        messages = [
            SimpleNamespace(type=aiohttp.WSMsgType.TEXT, data=payload)
            for payload in _ws_messages(final_text="async-stream", request_id="req-a-stream")
        ]
        mock_ws = MockWS(messages)

        mock_ws_context = AsyncMock()
        mock_ws_context.__aenter__.return_value = mock_ws

        mock_session = MagicMock()
        mock_session.ws_connect.return_value = mock_ws_context
        mock_session.close = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch("builtins.open", mock_open(read_data=b"fake_audio")):
                with patch.object(
                    client.stt, "_convert_audio_to_pcm16", return_value=mock_audio_data
                ):
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        result = await client.stt.transcribe_async(
                            "sample.wav",
                            model="indus-stt-hi-en",
                            streaming=True,
                            noise_cancellation=True,
                            language="hindi",
                        )

        assert result.text == "async-stream"
        assert any("only supported in non-streaming" in str(w.message) for w in caught)
        await client.stt.close()


class TestSTTResponse:
    def test_add_segments_and_metrics_to_dict(self):
        response = STTResponse()
        response.add_segment("hello", start=0.0, end=0.5)
        response.set_final("hello", "req-1")
        response.set_metrics(buffer=1.2, transcription=0.4, total=0.6, rtf=0.3, request_id="req-1")

        data = response.to_dict()
        assert data["request_id"] == "req-1"
        assert data["segments"][0]["text"] == "hello"
        assert data["metrics"]["rtf"] == 0.3

    def test_error_and_completion_properties(self):
        response = STTResponse()
        response.set_error("boom")
        assert response.has_error
        assert response.error == "boom"

        response2 = STTResponse()
        response2.complete()
        assert response2.is_completed

    def test_str_and_repr(self):
        response = STTResponse()
        response.set_final("sample text", "req-2")
        assert str(response) == "sample text"
        assert "STTResponse" in repr(response)
