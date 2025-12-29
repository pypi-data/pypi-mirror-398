import av
import numpy as np
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Optional
from PIL import Image
from tqdm import tqdm

from openframe.element import FrameElement
from openframe.audio import AudioClip, AudioLayout
from openframe.util import Layer


@dataclass
class Scene:
    """Hold a set of elements or child scenes and export their combined timeline."""
    class ContentType(Enum):
        ELEMENTS = "elements"
        SCENES = "scenes"

    start_at: float
    _elements: list[FrameElement] = field(default_factory=list)
    _scenes: list['Scene'] = field(default_factory=list)
    _audio: list[AudioClip] = field(default_factory=list)
    _content_type: Optional['Scene.ContentType'] = field(default=None, init=False)
    _duration: float = field(default=0.0, init=False)
    

    def add(self, element: FrameElement, layer: Layer=Layer.TOP) -> None:
        """Enqueue a frame element for later rendering.

        Args:
            element (FrameElement): Element that can draw itself.
        """
        self._ensure_content_type(self.ContentType.ELEMENTS)
        
        if layer == Layer.TOP:
            self._elements.append(element)
        elif layer == Layer.BOTTOM:
            self._elements.insert(0, element)

        self._update_duration(element.end_time)
        
    def add_scene(self, scene: 'Scene', layer: Layer=Layer.TOP) -> None:
        """Queue a nested scene and guard against mixing with frame elements.

        Args:
            scene (Scene): Scene whose timeline should be rendered as part of this scene.
        """
        self._ensure_content_type(self.ContentType.SCENES)
        
        if layer == Layer.TOP:
            self._scenes.append(scene)
        elif layer == Layer.BOTTOM:
            self._scenes.insert(0, scene)

        self._update_duration(scene.start_at + scene.duration)

    def add_audio(self, clip: AudioClip, layer: Layer=Layer.TOP) -> None:
        """Queue an audio clip for this scene.

        Args:
            clip (AudioClip): Audio clip to mix into the timeline.
        """
        if layer == Layer.TOP:
            self._audio.append(clip)
        elif layer == Layer.BOTTOM:
            self._audio.insert(0, clip)

        self._update_duration(clip.end_time)
        
    def _get_elements(self) -> list[FrameElement]:
        """Adjusts element start times and returns the configured element list.

        Returns:
            list[FrameElement]: Elements shifted according to this scene's start time.
        """
        if self._content_type == self.ContentType.ELEMENTS:
            return self._clone_with_offset(self._elements, self.start_at)

        if self._content_type == self.ContentType.SCENES:
            elements: list[FrameElement] = []
            for scene in self._scenes:
                child_elements = scene._get_elements()
                elements.extend(self._clone_with_offset(child_elements, self.start_at))
            return elements
        
        return []

    def _get_audio(self) -> list[AudioClip]:
        """Adjust audio start times and returns the configured audio list.

        Returns:
            list[AudioClip]: Audio clips shifted according to this scene's start time.
        """
        clips = self._clone_audio_with_offset(self._audio, self.start_at)

        if self._content_type != self.ContentType.SCENES:
            return clips

        for scene in self._scenes:
            child_clips = scene._get_audio()
            clips.extend(self._clone_audio_with_offset(child_clips, self.start_at))

        return clips
        
    @property
    def total_duration(self) -> float:
        return self.start_at + self._duration

    @property
    def duration(self) -> float:
        """Return the duration of this scene relative to its own start.

        Returns:
            float: Duration in seconds.
        """

        return self._duration
        

    @staticmethod
    def _clone_with_offset(elements: list[FrameElement], offset: float) -> list[FrameElement]:
        """Return copies of elements with their start times shifted.

        Args:
            elements (list[FrameElement]): Elements to clone.
            offset (float): Amount of seconds to add to each start time.

        Returns:
            list[FrameElement]: New elements with adjusted start times.
        """
        return [replace(element, start_time=element.start_time + offset) for element in elements]

    @staticmethod
    def _clone_audio_with_offset(clips: list[AudioClip], offset: float) -> list[AudioClip]:
        """Return copies of audio clips with their start times shifted.

        Args:
            clips (list[AudioClip]): Audio clips to clone.
            offset (float): Amount of seconds to add to each start time.

        Returns:
            list[AudioClip]: New audio clips with adjusted start times.
        """
        return [replace(clip, start_time=clip.start_time + offset) for clip in clips]

    def _update_duration(self, end_time: float) -> None:
        """Update cached duration if the new end time exceeds it.

        Args:
            end_time: End time relative to this scene's timeline.
        """

        if end_time > self._duration:
            self._duration = end_time

    def _ensure_content_type(self, desired: 'Scene.ContentType') -> None:
        """Set the content type once and prevent mixing elements with scenes.

        Args:
            desired (Scene.ContentType): Intended content type for this scene.
        """
        if self._content_type is None:
            self._content_type = desired
            return
        if self._content_type is not desired:
            raise ValueError(
                "Scene already configured for "
                f"{self._content_type.value}, cannot add {desired.value}."
            )

    def _create_frame(self, t: float, width: int, height: int) -> np.ndarray:
        """Render all visible clips onto a single RGBA frame.

        Args:
            t (float): Current time in seconds for visibility checks.
            width (int): Frame width in pixels.
            height (int): Frame height in pixels.

        Returns:
            np.ndarray: Frame image data in RGBA format.
        """

        img = Image.new('RGBA', (width, height), (0, 0, 0, 255))

        for clip in self._elements:
            if clip.is_visible(t):
                clip.render(img, t)

        return np.array(img)

    def render(
        self, 
        width: int = 1920, 
        height: int = 1080, 
        fps: int = 30, 
        output_path: str = "output.mp4"
    ) -> None:
        """Encode all configured elements into a video file.

        Args:
            total_duration (float): Total duration of the exported video in seconds.
            width (int): Frame width in pixels.
            height (int): Frame height in pixels.
            fps (int): Frames per second for the exported video.
            output_path (str): File path to write the encoded video into.

        Returns:
            None
        """
        output_container = av.open(output_path, mode='w')
        stream = output_container.add_stream('h264', rate=fps)
        stream.codec_context.options = {
            "preset": "ultrafast",
            "tune": "zerolatency",
        }
        stream.pix_fmt = 'yuv420p'
        stream.width, stream.height = width, height
        total_frames = int(self.total_duration * fps)
        
        self._elements = self._get_elements()
        audio_clips = self._get_audio()
        audio_stream = None

        if audio_clips:
            audio_stream = output_container.add_stream('aac', rate=44100)
            audio_stream.layout = AudioLayout.MONO.value

        for i in tqdm(range(total_frames), desc="Exporting", unit="frame", ncols=100):
            t = i / fps
            frame_data = self._create_frame(t, width, height)
            frame = av.VideoFrame.from_ndarray(frame_data, format='rgba')
            for packet in stream.encode(frame):
                output_container.mux(packet)

        for packet in stream.encode():
            output_container.mux(packet)

        if audio_stream is not None:
            self._encode_audio(output_container, audio_stream, audio_clips)

        output_container.close()

    def _encode_audio(
        self,
        container: av.container.output.OutputContainer,
        stream: av.audio.stream.AudioStream,
        clips: list[AudioClip],
    ) -> None:
        """Mix audio clips and encode them into the output container.

        Args:
            container (av.container.output.OutputContainer): Output container.
            stream (av.audio.stream.AudioStream): Target audio stream.
            clips (list[AudioClip]): Audio clips to mix.
        """
        sample_rate = stream.rate
        channels = 1
        total_samples = int(self.total_duration * sample_rate)
        mix = np.zeros((total_samples, channels), dtype=np.float32)

        for clip in clips:
            clip_data = clip.render(sample_rate, channels)
            start_idx = int(clip.start_time * sample_rate)
            end_idx = min(total_samples, start_idx + clip_data.shape[0])
            mix[start_idx:end_idx] += clip_data[: end_idx - start_idx]

        mix = np.clip(mix, -1.0, 1.0)
        frame_size = stream.codec_context.frame_size or 1024
        layout = stream.layout.name

        for start in range(0, total_samples, frame_size):
            end = min(total_samples, start + frame_size)
            chunk = mix[start:end]

            if end - start < frame_size:
                pad = np.zeros((frame_size - (end - start), channels), dtype=np.float32)
                chunk = np.vstack((chunk, pad))

            frame = av.AudioFrame.from_ndarray(chunk.T, format="fltp", layout=layout)
            frame.sample_rate = sample_rate
            for packet in stream.encode(frame):
                container.mux(packet)

        for packet in stream.encode():
            container.mux(packet)
