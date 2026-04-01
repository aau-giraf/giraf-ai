"""Shared audio utilities for TTS adapters."""

import io
import struct


def pcm_to_wav(pcm: bytes, sample_rate: int = 24000) -> bytes:
    """Wrap raw 16-bit mono PCM in a WAV header."""
    buf = io.BytesIO()
    data_size = len(pcm)
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(pcm)
    return buf.getvalue()


def make_wav_silence(duration_ms: int = 500, sample_rate: int = 16000) -> bytes:
    """Generate a minimal silent WAV file."""
    num_samples = sample_rate * duration_ms // 1000
    pcm = b"\x00" * (num_samples * 2)  # 16-bit mono
    return pcm_to_wav(pcm, sample_rate)
