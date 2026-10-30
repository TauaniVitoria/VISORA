"""
Testes de suporte a streams RTSP/IP no VideoReader e ingestão no ALPR.
"""

import pytest
from unittest.mock import MagicMock, patch
from alpr.video_reader import VideoReader, VideoMetadata

def test_video_reader_detects_rtsp_stream():
    # Testa detecção de protocolo RTSP sem exigir câmera física ligada
    with patch("cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.get.side_effect = lambda prop: 1920 if prop == 3 else 1080 if prop == 4 else 30.0 if prop == 5 else 0
        mock_cap.return_value = mock_instance

        reader = VideoReader("rtsp://192.168.1.50:554/live/ch0")
        assert reader.is_stream is True
        assert reader.metadata.is_stream is True
        assert reader.metadata.width == 1920
        assert reader.metadata.height == 1080
        assert reader.metadata.fps == 30.0
        reader.release()
