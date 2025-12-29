from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

import av
import numpy as np


class AudioLayout(Enum):
    MONO = "mono"
    STEREO = "stereo"

@lru_cache(maxsize=64)
def _source_duration_cached(path: str) -> float:
    """Return cached duration for the given audio source.

    Args:
        path: File path for the audio asset.

    Returns:
        float: Duration in seconds.
    """

    container = av.open(path)
    stream = container.streams.audio[0]
    duration = float(stream.duration * stream.time_base)
    container.close()
    return duration


@lru_cache(maxsize=16)
def _decode_audio_cached(path: str, sample_rate: int, layout: str) -> np.ndarray:
    """Decode and cache audio samples for a given source and format.

    Args:
        path: File path for the audio asset.
        sample_rate: Target sample rate.
        layout: Audio layout name.

    Returns:
        np.ndarray: Audio samples shaped as (samples, channels).
    """

    container = av.open(path)
    stream = container.streams.audio[0]
    resampler = av.AudioResampler(format="fltp", layout=layout, rate=sample_rate)
    frames: list[np.ndarray] = []

    for frame in container.decode(stream):
        resampled = resampler.resample(frame) or []
        if not isinstance(resampled, list):
            resampled = [resampled]
        frames.extend([chunk.to_ndarray() for chunk in resampled])

    container.close()

    merged = np.concatenate(frames, axis=1)
    return merged.T.astype(np.float32)


@dataclass(kw_only=True)
class AudioClip:
    """Represent an audio segment placed on the scene timeline.

    The clip can repeat automatically when loop_enable is True and the requested duration exceeds the source length.
    """

    source_path: str
    start_time: float
    source_start: float = 0
    source_end: float | None = None
    loop_enable: bool = False
    fade_in_duration: float = 0.0
    fade_out_duration: float = 0.0
    volume: float = 1.0

    @property
    def duration(self) -> float:
        """Return duration of the clip in seconds.

        Returns:
            float: Duration in seconds.
        """
        end = self.source_end if self.source_end is not None else self._source_duration()
        return end - self.source_start

    @property
    def end_time(self) -> float:
        """Return the timeline end time for this clip.

        Returns:
            float: End time in seconds.
        """
        return self.start_time + self.duration

    def render(self, sample_rate: int, channels: int) -> np.ndarray:
        """Decode and return audio samples aligned to the requested format.

        Args:
            sample_rate (int): Target sample rate.
            channels (int): Target number of channels (ignored; mono only).

        Returns:
            np.ndarray: Audio samples shaped as (samples, channels).
        """
        audio = self._decode_audio(sample_rate, AudioLayout.MONO.value)
        start_idx = int(self.source_start * sample_rate)
        end_idx = int(self.source_end * sample_rate) if self.source_end is not None else audio.shape[0]
        desired_samples = max(0, int(self.duration * sample_rate))
        segment = audio[start_idx:end_idx]

        if not self.loop_enable or desired_samples <= segment.shape[0]:
            trimmed = segment[:desired_samples]
        elif desired_samples == 0 or segment.shape[0] == 0:
            channels_count = audio.shape[1]
            trimmed = np.zeros((desired_samples, channels_count), dtype=np.float32)
        else:
            repetitions = desired_samples // segment.shape[0]
            remainder = desired_samples % segment.shape[0]
            chunks = [segment] * repetitions
            if remainder:
                chunks.append(segment[:remainder])
            trimmed = np.concatenate(chunks, axis=0)

        return self._apply_fades(trimmed, sample_rate)

    def _apply_fades(self, samples: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply fade-in and fade-out envelopes to the rendered samples.

        Args:
            samples: The raw samples to shape.
            sample_rate: Number of samples per second used for sizing fades.

        Returns:
            np.ndarray: Samples with fade envelopes applied.
        """
        if samples.shape[0] == 0:
            return samples

        total_samples = samples.shape[0]
        envelope = np.ones(total_samples, dtype=np.float32)

        fade_in_samples = min(total_samples, int(self.fade_in_duration * sample_rate))
        if fade_in_samples > 0:
            envelope[:fade_in_samples] = np.linspace(
                0.0,
                1.0,
                fade_in_samples,
                dtype=np.float32,
                endpoint=False,
            )

        fade_out_samples = min(total_samples, int(self.fade_out_duration * sample_rate))
        if fade_out_samples > 0:
            fade_out_curve = np.linspace(
                1.0,
                0.0,
                fade_out_samples,
                dtype=np.float32,
                endpoint=False,
            )
            envelope[-fade_out_samples:] *= fade_out_curve

        return samples * envelope[:, None] * self.volume

    def _source_duration(self) -> float:
        """Return source audio duration in seconds.

        Returns:
            float: Duration in seconds.
        """
        return _source_duration_cached(self.source_path)

    def _decode_audio(self, sample_rate: int, layout: str) -> np.ndarray:
        """Decode audio file into a normalized float32 array.

        Args:
            sample_rate (int): Target sample rate.
            layout (str): Audio layout name.

        Returns:
            np.ndarray: Audio samples shaped as (samples, channels).
        """
        return _decode_audio_cached(self.source_path, sample_rate, layout)
