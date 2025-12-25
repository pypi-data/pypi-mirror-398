import enum
from typing import Annotated, overload

import numpy
from numpy.typing import NDArray


class Format(enum.Enum):
    MJPEG = 0

    YUY2 = 1

    NV12 = 2

    RGB = 3

    RGBA = 4

class DeviceInfo:
    @property
    def name(self) -> str: ...

    @property
    def unique_id(self) -> str: ...

    @property
    def index(self) -> int: ...

    def __repr__(self) -> str: ...

class FormatInfo:
    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    @property
    def fps(self) -> int: ...

    @property
    def format(self) -> Format: ...

    def __repr__(self) -> str: ...

class Frame:
    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    @property
    def format(self) -> Format: ...

    @property
    def timestamp(self) -> int: ...

    def to_nv12(self) -> tuple[Annotated[NDArray[numpy.uint8], dict(shape=(None, None))], Annotated[NDArray[numpy.uint8], dict(shape=(None, None))]]:
        """Get NV12 Y and UV planes as (Y, UV) tuple"""

    def to_yuy2(self) -> Annotated[NDArray[numpy.uint8], dict(shape=(None, None, None))]:
        """Get YUY2 data as (H, W, 2) array"""

    def to_rgb(self) -> Annotated[NDArray[numpy.uint8], dict(shape=(None, None, None))]:
        """Get RGB data as (H, W, 3) array"""

    def to_rgba(self) -> Annotated[NDArray[numpy.uint8], dict(shape=(None, None, None))]:
        """Get RGBA data as (H, W, 4) array"""

    def native_buffer(self) -> object:
        """Get native buffer as PyCapsule (macOS: CVPixelBufferRef, Linux: None)"""

class Device:
    def start(self, width: int, height: int, fps: int, capture_format: Format = Format.MJPEG, output_format: Format | None = None) -> None:
        """Start capturing"""

    def stop(self) -> None:
        """Stop capturing"""

    def get_frame(self) -> Frame:
        """Get next frame"""

    @property
    def is_running(self) -> bool: ...

    @property
    def info(self) -> DeviceInfo: ...

    def get_supported_formats(self) -> list[FormatInfo]:
        """Get list of FormatInfo"""

    def __enter__(self) -> Device:
        """Enter context manager"""

    def __exit__(self, arg0: object | None, arg1: object | None, arg2: object | None) -> None:
        """Exit context manager"""

def list_devices() -> list[DeviceInfo]:
    """List available UVC devices"""

@overload
def open(index: int, on_connected: object | None = None, on_disconnected: object | None = None) -> Device:
    """Open device by index"""

@overload
def open(info: DeviceInfo, on_connected: object | None = None, on_disconnected: object | None = None) -> Device:
    """Open device by DeviceInfo"""
