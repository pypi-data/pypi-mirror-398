import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod

class _Transcoder(ABC, metaclass=abc.ABCMeta):
    """Abstract base class for data transcoders."""
    SIGNATURES: tuple[bytes, ...]
    @classmethod
    @abstractmethod
    def transcode(cls, data: bytes) -> bytes:
        """Convert the data and return the converted bytes."""

class _TiffTranscoder(_Transcoder):
    """Transcoder for converting TIFF images into PNG format."""
    SIGNATURES: Incomplete
    @classmethod
    def transcode(cls, data: bytes) -> bytes:
        """Convert TIFF image data to PNG format."""

class _NpyTranscoder(_Transcoder):
    """Transcoder for interpreting certain NumPy arrays as PNG images."""
    SIGNATURES: Incomplete
    @classmethod
    def transcode(cls, data: bytes) -> bytes:
        """Convert NumPy array data to PNG format."""

def get_transcoder(data: bytes) -> type[_Transcoder] | None:
    """Retrieve a matching transcoder for the given data if any."""
