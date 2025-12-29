from collections.abc import Callable
import enum
from typing import overload

import numpy
import typing_extensions
import webcodecs


class CodecState(enum.Enum):
    UNCONFIGURED = 0

    CONFIGURED = 1

    CLOSED = 2

class LatencyMode(enum.Enum):
    QUALITY = 0

    REALTIME = 1

class VideoEncoderBitrateMode(enum.Enum):
    CONSTANT = 0

    VARIABLE = 1

    QUANTIZER = 2

class BitrateMode(enum.Enum):
    CONSTANT = 0

    VARIABLE = 1

class AlphaOption(enum.Enum):
    KEEP = 0

    DISCARD = 1

class HardwareAcceleration(enum.Enum):
    NO_PREFERENCE = 0

    PREFER_HARDWARE = 1

    PREFER_SOFTWARE = 2

class VideoColorPrimaries(enum.Enum):
    BT709 = 0

    BT470BG = 1

    SMPTE170M = 2

    BT2020 = 3

    SMPTE432 = 4

class VideoTransferCharacteristics(enum.Enum):
    BT709 = 0

    SMPTE170M = 1

    IEC61966_2_1 = 2

    LINEAR = 3

    PQ = 4

    HLG = 5

class VideoMatrixCoefficients(enum.Enum):
    RGB = 0

    BT709 = 1

    BT470BG = 2

    SMPTE170M = 3

    BT2020_NCL = 4

class PlaneLayout:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, offset: int, stride: int) -> None: ...

    @property
    def offset(self) -> int: ...

    @offset.setter
    def offset(self, arg: int, /) -> None: ...

    @property
    def stride(self) -> int: ...

    @stride.setter
    def stride(self, arg: int, /) -> None: ...

class DOMRect:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, x: float, y: float, width: float, height: float) -> None: ...

    @property
    def x(self) -> float: ...

    @x.setter
    def x(self, arg: float, /) -> None: ...

    @property
    def y(self) -> float: ...

    @y.setter
    def y(self, arg: float, /) -> None: ...

    @property
    def width(self) -> float: ...

    @width.setter
    def width(self, arg: float, /) -> None: ...

    @property
    def height(self) -> float: ...

    @height.setter
    def height(self, arg: float, /) -> None: ...

class VideoColorSpace:
    def __init__(self) -> None: ...

    @property
    def primaries(self) -> str | None: ...

    @primaries.setter
    def primaries(self, arg: str, /) -> None: ...

    @property
    def transfer(self) -> str | None: ...

    @transfer.setter
    def transfer(self, arg: str, /) -> None: ...

    @property
    def matrix(self) -> str | None: ...

    @matrix.setter
    def matrix(self, arg: str, /) -> None: ...

    @property
    def full_range(self) -> bool | None: ...

    @full_range.setter
    def full_range(self, arg: bool, /) -> None: ...

class AudioDecoderSupport:
    def __init__(self) -> None: ...

    def __getitem__(self, arg: str, /) -> object: ...

class VideoDecoderSupport:
    def __init__(self) -> None: ...

    def __getitem__(self, arg: str, /) -> object: ...

class AudioEncoderSupport:
    def __init__(self) -> None: ...

    def __getitem__(self, arg: str, /) -> object: ...

class VideoEncoderSupport:
    def __init__(self) -> None: ...

    def __getitem__(self, arg: str, /) -> object: ...

class VideoPixelFormat(enum.Enum):
    I420 = 0

    I422 = 1

    I444 = 2

    NV12 = 3

    RGBA = 4

    BGRA = 5

    RGB = 6

    BGR = 7

class VideoFrame:
    @overload
    def __init__(self, data: numpy.typing.NDArray[numpy.uint8], init: VideoFrameBufferInit, /) -> None: ...

    @overload
    def __init__(self, native_buffer: typing_extensions.CapsuleType, init: dict) -> None: ...

    @property
    def format(self, /) -> VideoPixelFormat: ...

    @property
    def timestamp(self, /) -> int: ...

    @property
    def duration(self, /) -> int: ...

    @duration.setter
    def duration(self, value: int, /) -> None: ...

    @property
    def coded_width(self, /) -> int: ...

    @property
    def coded_height(self, /) -> int: ...

    @property
    def visible_rect(self, /) -> DOMRect | None: ...

    @property
    def display_width(self, /) -> int: ...

    @property
    def display_height(self, /) -> int: ...

    @property
    def color_space(self, /) -> VideoColorSpace | None: ...

    @property
    def rotation(self, /) -> int: ...

    @property
    def flip(self, /) -> bool: ...

    def metadata(self, /) -> dict: ...

    @property
    def native_buffer(self, /) -> object | None: ...

    @native_buffer.setter
    def native_buffer(self, value: object, /) -> None: ...

    def plane(self, plane_index: int, /) -> numpy.typing.NDArray[numpy.uint8]: ...

    def allocation_size(self, options: VideoFrameCopyToOptions | None = None, /) -> int: ...

    def copy_to(self, destination: numpy.typing.NDArray[numpy.uint8], options: VideoFrameCopyToOptions | None = None, /) -> list[PlaneLayout]: ...

    def planes(self, /) -> tuple[numpy.typing.NDArray[numpy.uint8], numpy.typing.NDArray[numpy.uint8], numpy.typing.NDArray[numpy.uint8]]: ...

    def close(self, /) -> None: ...

    @property
    def is_closed(self, /) -> bool: ...

    def clone(self, /) -> VideoFrame: ...

    def __enter__(self) -> VideoFrame: ...

    def __exit__(self, exc_type: object | None, exc_val: object | None, exc_tb: object | None) -> None: ...

class AudioSampleFormat(enum.Enum):
    U8 = 0

    S16 = 1

    S32 = 2

    F32 = 3

    U8_PLANAR = 4

    S16_PLANAR = 5

    S32_PLANAR = 6

    F32_PLANAR = 7

class AudioData:
    def __init__(self, init: webcodecs.AudioDataInit, /) -> None: ...

    @property
    def number_of_channels(self, /) -> int: ...

    @property
    def sample_rate(self, /) -> int: ...

    @property
    def number_of_frames(self, /) -> int: ...

    @property
    def format(self, /) -> AudioSampleFormat: ...

    @property
    def timestamp(self, /) -> int: ...

    @property
    def duration(self, /) -> int: ...

    def get_channel_data(self, channel: int, /) -> numpy.typing.NDArray: ...

    def copy_to(self, destination: numpy.typing.NDArray, options: webcodecs.AudioDataCopyToOptions) -> None: ...

    def allocation_size(self, options: webcodecs.AudioDataCopyToOptions, /) -> int: ...

    def close(self, /) -> None: ...

    @property
    def is_closed(self, /) -> bool: ...

    def clone(self, /) -> AudioData: ...

    def __enter__(self) -> AudioData: ...

    def __exit__(self, exc_type: object | None, exc_val: object | None, exc_tb: object | None) -> None: ...

class EncodedVideoChunkType(enum.Enum):
    KEY = 0

    DELTA = 1

class EncodedVideoChunk:
    def __init__(self, init: webcodecs.EncodedVideoChunkInit) -> None: ...

    @property
    def type(self, /) -> EncodedVideoChunkType: ...

    @property
    def timestamp(self, /) -> int: ...

    @property
    def duration(self, /) -> int: ...

    @property
    def byte_length(self, /) -> int: ...

    def copy_to(self, destination: numpy.typing.NDArray[numpy.uint8]) -> None: ...

class EncodedAudioChunkType(enum.Enum):
    KEY = 0

    DELTA = 1

class EncodedAudioChunk:
    def __init__(self, init: webcodecs.EncodedAudioChunkInit) -> None: ...

    @property
    def type(self, /) -> EncodedAudioChunkType: ...

    @property
    def timestamp(self, /) -> int: ...

    @property
    def duration(self, /) -> int: ...

    @property
    def byte_length(self, /) -> int: ...

    def copy_to(self, destination: numpy.typing.NDArray[numpy.uint8]) -> None: ...

class VideoDecoder:
    def __init__(self, output: Callable[[VideoFrame], None], error: Callable[[str], None], /) -> None: ...

    def configure(self, config: webcodecs.VideoDecoderConfig, /) -> None: ...

    def decode(self, chunk: EncodedVideoChunk, /) -> None: ...

    def flush(self, /) -> None: ...

    def reset(self, /) -> None: ...

    def close(self, /) -> None: ...

    @property
    def state(self, /) -> CodecState: ...

    @property
    def decode_queue_size(self, /) -> int: ...

    @staticmethod
    def is_config_supported(config: webcodecs.VideoDecoderConfig, /) -> webcodecs.VideoDecoderSupport: ...

    def on_output(self, callback: Callable[[VideoFrame], None], /) -> None: ...

    def on_error(self, callback: Callable[[str], None], /) -> None: ...

    def on_dequeue(self, callback: Callable[[], None], /) -> None: ...

class AudioDecoder:
    def __init__(self, output: Callable[[AudioData], None], error: Callable[[str], None], /) -> None: ...

    def configure(self, config: webcodecs.AudioDecoderConfig, /) -> None: ...

    def decode(self, chunk: EncodedAudioChunk, /) -> None: ...

    def flush(self, /) -> None: ...

    def reset(self, /) -> None: ...

    def close(self, /) -> None: ...

    @property
    def state(self, /) -> CodecState: ...

    @property
    def decode_queue_size(self, /) -> int: ...

    @staticmethod
    def is_config_supported(config: webcodecs.AudioDecoderConfig, /) -> webcodecs.AudioDecoderSupport: ...

    def on_output(self, callback: Callable[[AudioData], None], /) -> None: ...

    def on_error(self, callback: Callable[[str], None], /) -> None: ...

    def on_dequeue(self, callback: Callable[[], None], /) -> None: ...

class VideoEncoder:
    def __init__(self, output: Callable[[EncodedVideoChunk], None], error: Callable[[str], None], /) -> None: ...

    def configure(self, config: webcodecs.VideoEncoderConfig, /) -> None: ...

    @overload
    def encode(self, frame: VideoFrame, /) -> None: ...

    @overload
    def encode(self, frame: VideoFrame, options: webcodecs.VideoEncoderEncodeOptions, /) -> None: ...

    def flush(self, /) -> None: ...

    def reset(self, /) -> None: ...

    def close(self, /) -> None: ...

    @property
    def state(self, /) -> CodecState: ...

    @property
    def encode_queue_size(self, /) -> int: ...

    @staticmethod
    def is_config_supported(config: webcodecs.VideoEncoderConfig, /) -> webcodecs.VideoEncoderSupport: ...

    def on_output(self, callback: Callable[[EncodedVideoChunk], None], /) -> None: ...

    def on_error(self, callback: Callable[[str], None], /) -> None: ...

    def on_dequeue(self, callback: Callable[[], None], /) -> None: ...

class AudioEncoder:
    def __init__(self, output: Callable[[EncodedAudioChunk], None], error: Callable[[str], None], /) -> None: ...

    def configure(self, config: webcodecs.AudioEncoderConfig, /) -> None: ...

    def encode(self, data: AudioData, /) -> None: ...

    def flush(self, /) -> None: ...

    def reset(self, /) -> None: ...

    def close(self, /) -> None: ...

    @property
    def state(self, /) -> CodecState: ...

    @property
    def encode_queue_size(self, /) -> int: ...

    @staticmethod
    def is_config_supported(config: webcodecs.AudioEncoderConfig, /) -> webcodecs.AudioEncoderSupport: ...

    def on_output(self, callback: Callable[[EncodedAudioChunk], None], /) -> None: ...

    def on_error(self, callback: Callable[[str], None], /) -> None: ...

    def on_dequeue(self, callback: Callable[[], None], /) -> None: ...

class HardwareAccelerationEngine(enum.Enum):
    NONE = 0

    APPLE_VIDEO_TOOLBOX = 1

    NVIDIA_VIDEO_CODEC = 2

    INTEL_VPL = 3

    AMD_AMF = 4

class ImageTrack:
    @property
    def animated(self, /) -> bool: ...

    @property
    def frame_count(self, /) -> int: ...

    @property
    def repetition_count(self, /) -> float: ...

    @property
    def selected(self, /) -> bool: ...

    @selected.setter
    def selected(self, /) -> bool: ...

class ImageTrackList:
    def __getitem__(self, index: int, /) -> ImageTrack | None: ...

    def __len__(self, /) -> int: ...

    @property
    def length(self, /) -> int: ...

    @property
    def selected_index(self, /) -> int: ...

    @property
    def selected_track(self, /) -> ImageTrack | None: ...

    @property
    def is_ready(self, /) -> bool: ...

class ImageDecoder:
    def __init__(self, init: dict, /) -> None: ...

    def decode(self, options: dict = {}, /) -> dict: ...

    def reset(self, /) -> None: ...

    def close(self, /) -> None: ...

    @property
    def type(self, /) -> str: ...

    @property
    def complete(self, /) -> bool: ...

    @property
    def is_complete(self, /) -> bool: ...

    @property
    def tracks(self, /) -> ImageTrackList: ...

    @property
    def is_closed(self, /) -> bool: ...

    @staticmethod
    def is_type_supported(type: str) -> bool: ...
