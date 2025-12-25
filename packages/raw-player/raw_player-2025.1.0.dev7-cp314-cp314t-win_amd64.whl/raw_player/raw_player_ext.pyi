from collections.abc import Callable
from typing import Any, overload

import numpy


class AudioPlayer:
    def __init__(self) -> None: ...

    def enqueue_audio(self, pcm: numpy.ndarray, pts_us: int, sample_rate: int) -> None:
        """
        Enqueue audio samples for playback.

        Args:
            pcm: Audio data as int16 or float32 array.
                 Shape: (frames, channels) or (frames,) for mono.
            pts_us: Presentation timestamp in microseconds.
            sample_rate: Sample rate in Hz (e.g., 48000).
        """

    def play(self) -> None:
        """Start or resume playback."""

    def pause(self) -> None:
        """Pause playback."""

    def stop(self) -> None:
        """Stop playback and clear the queue."""

    def stats(self) -> dict[str, Any]:
        """
        Get playback statistics.

        Returns:
            Dictionary with keys:
                - audio_queue_size: Number of chunks in queue
                - audio_buffer_ms: Audio buffer length in milliseconds
                - chunks_played: Number of chunks played
                - audio_clock_us: Current audio clock in microseconds
                - sample_rate: Sample rate in Hz
                - channels: Number of channels
                - is_float: True if float32 format
                - total_samples_enqueued: Total samples enqueued
                - total_samples_played: Total samples played
                - elapsed_time_ms: Elapsed time in milliseconds
                - audio_bitrate_kbps: Audio bitrate in kbps
        """

    @property
    def is_playing(self) -> bool:
        """Whether audio is currently playing."""

    @property
    def volume(self, value: float) -> None:
        """Playback volume (0.0 to 1.0)."""

    @volume.setter
    def volume(self, value: float) -> None: ...

class VideoPlayer:
    def __init__(self, width: int = 960, height: int = 540, title: str = 'Raw Player') -> None:
        """
        Create a video player with the specified window size.

        Args:
            width: Window width (default: 960)
            height: Window height (default: 540)
            title: Window title (default: 'Raw Player')
        """

    def enqueue_video_i420(self, y: numpy.ndarray, u: numpy.ndarray, v: numpy.ndarray, pts_us: int) -> None:
        """
        Enqueue an I420 video frame.

        Args:
            y: Y plane, uint8 (H, W)
            u: U plane, uint8 (H/2, W/2)
            v: V plane, uint8 (H/2, W/2)
            pts_us: Presentation timestamp in microseconds
        """

    @overload
    def enqueue_video_nv12(self, y: numpy.ndarray, uv: numpy.ndarray, pts_us: int) -> None:
        """
        Enqueue an NV12 video frame.

        Args:
            y: Y plane, uint8 (H, W)
            uv: UV plane, uint8 (H/2, W)
            pts_us: Presentation timestamp in microseconds
        """

    @overload
    def enqueue_video_nv12(self, native_buffer: object, pts_us: int) -> None:
        """
        Enqueue an NV12 video frame from native buffer.

        Args:
            native_buffer: PyCapsule containing CVPixelBufferRef (macOS)
            pts_us: Presentation timestamp in microseconds
        """

    @overload
    def enqueue_video_yuy2(self, data: numpy.ndarray, pts_us: int) -> None:
        """
        Enqueue a YUY2 video frame.

        Args:
            data: Packed YUY2 data, uint8 (H, W, 2)
            pts_us: Presentation timestamp in microseconds
        """

    @overload
    def enqueue_video_yuy2(self, native_buffer: object, pts_us: int) -> None:
        """
        Enqueue a YUY2 video frame from native buffer.

        Args:
            native_buffer: PyCapsule containing CVPixelBufferRef (macOS)
            pts_us: Presentation timestamp in microseconds
        """

    def enqueue_video_rgba(self, data: numpy.ndarray, pts_us: int) -> None:
        """
        Enqueue an RGBA video frame.

        Args:
            data: RGBA data, uint8 (H, W, 4)
            pts_us: Presentation timestamp in microseconds
        """

    def enqueue_video_bgra(self, data: numpy.ndarray, pts_us: int) -> None:
        """
        Enqueue a BGRA video frame.

        Args:
            data: BGRA data, uint8 (H, W, 4)
            pts_us: Presentation timestamp in microseconds
        """

    def enqueue_audio(self, pcm: numpy.ndarray, pts_us: int, sample_rate: int) -> None:
        """
        Enqueue audio data.

        Args:
            pcm: Audio samples, int16 or float32, shape (frames,) or (frames, channels)
            pts_us: Presentation timestamp in microseconds
            sample_rate: Sample rate in Hz
        """

    def play(self) -> None:
        """Start or resume playback."""

    def pause(self) -> None:
        """Pause playback."""

    def stop(self) -> None:
        """Stop playback and clear queues."""

    def close(self) -> None:
        """Close the window and release resources."""

    def poll_events(self) -> bool:
        """
        Poll window events and render next frame. Returns False if window was closed.
        """

    @property
    def is_open(self) -> bool:
        """Whether the window is open."""

    @property
    def is_playing(self) -> bool:
        """Whether playback is active."""

    @property
    def width(self) -> int:
        """Window width."""

    @property
    def height(self) -> int:
        """Window height."""

    @property
    def title(self, value: str) -> None:
        """Window title."""

    @title.setter
    def title(self, value: str) -> None: ...

    @property
    def renderer_name(self) -> str:
        """GPU renderer name (e.g., 'metal', 'vulkan')."""

    @property
    def volume(self, value: float) -> None:
        """Playback volume (0.0 to 1.0)."""

    @volume.setter
    def volume(self, value: float) -> None: ...

    def set_key_callback(self, callback: Callable[[int], bool] | None) -> None:
        """
        Set a callback for key events.

        The callback receives the key code and returns True to continue,
        or False to close the window (poll_events will return False).
        Pass None to remove the callback.

        Args:
            callback: Function (key: int) -> bool, or None
        """

    def stats(self) -> dict[str, Any]:
        """
        Get playback statistics.

        Returns:
            Dictionary with keys:
                - video_queue_size: Number of frames in video queue
                - audio_queue_ms: Audio queue length in milliseconds
                - dropped_frames: Number of dropped frames
                - repeated_frames: Number of repeated frames
                - video_pts_us: Last rendered video PTS
                - audio_pts_us: Current audio playback PTS
                - sync_diff_us: Audio-video sync difference
                - current_video_width: Current video width
                - current_video_height: Current video height
                - current_fps: Current FPS
                - total_frames_enqueued: Total frames enqueued
                - total_frames_rendered: Total frames rendered
                - video_buffer_ms: Video buffer time in milliseconds
                - elapsed_time_ms: Elapsed time in milliseconds
                - video_bitrate_kbps: Video bitrate in kbps
        """

    @property
    def max_video_queue_size(self, value: int) -> None:
        """
        Maximum video queue size.

        When enqueue_video_* is called and the queue size exceeds this limit,
        older frames are dropped to maintain low latency.
        Set to 0 to disable the limit (default: 5).
        """

    @max_video_queue_size.setter
    def max_video_queue_size(self, value: int) -> None: ...

    def drain_video(self) -> None:
        """
        Clear the video queue and reset timing.

        Use this to recover from accumulated latency.
        """

def get_version() -> str:
    """Get the SDL version string."""

def get_audio_driver() -> str:
    """Get the current audio driver name."""

def get_video_driver() -> str:
    """Get the current video driver name."""

def get_gpu_driver() -> str:
    """Get the primary GPU driver name (e.g., 'metal', 'vulkan', 'd3d12')."""

def get_num_gpu_drivers() -> int:
    """Get the number of available GPU drivers."""

def get_all_gpu_drivers() -> list[str]:
    """Get all available GPU driver names."""
