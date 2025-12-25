"""Compression utilities for artifact storage."""

import gzip
import lz4.frame
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Protocol


class CompressionType(str, Enum):
    """Supported compression algorithms."""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZLIB = "zlib"


class Compressor(Protocol):
    """Protocol for compression algorithms."""

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """Compress data."""
        pass

    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """Decompress data."""
        pass

    @property
    @abstractmethod
    def extension(self) -> str:
        """File extension for compressed files."""
        pass


class NoCompression:
    """No compression (passthrough)."""

    def compress(self, data: bytes) -> bytes:
        return data

    def decompress(self, data: bytes) -> bytes:
        return data

    @property
    def extension(self) -> str:
        return ""


class GzipCompressor:
    """GZIP compression with configurable compression level."""

    def __init__(self, level: int = 6):
        self.level = max(1, min(9, level))  # Clamp between 1-9

    def compress(self, data: bytes) -> bytes:
        return gzip.compress(data, compresslevel=self.level)

    def decompress(self, data: bytes) -> bytes:
        return gzip.decompress(data)

    @property
    def extension(self) -> str:
        return ".gz"


class LZ4Compressor:
    """LZ4 compression for fast compression/decompression."""

    def __init__(self, compression_level: int = 0):
        self.compression_level = compression_level

    def compress(self, data: bytes) -> bytes:
        return lz4.frame.compress(
            data,
            compression_level=self.compression_level,
            block_size=lz4.frame.BLOCKSIZE_MAX1MB
        )

    def decompress(self, data: bytes) -> bytes:
        return lz4.frame.decompress(data)

    @property
    def extension(self) -> str:
        return ".lz4"


class ZlibCompressor:
    """ZLIB compression with configurable compression level."""

    def __init__(self, level: int = 6):
        self.level = max(1, min(9, level))

    def compress(self, data: bytes) -> bytes:
        return zlib.compress(data, level=self.level)

    def decompress(self, data: bytes) -> bytes:
        return zlib.decompress(data)

    @property
    def extension(self) -> str:
        return ".zlib"


class CompressionManager:
    """Manages compression algorithms and selection."""

    def __init__(self):
        self._compressors = {
            CompressionType.NONE: NoCompression(),
            CompressionType.GZIP: GzipCompressor(),
            CompressionType.LZ4: LZ4Compressor(),
            CompressionType.ZLIB: ZlibCompressor(),
        }

    def get_compressor(self, compression_type: CompressionType) -> Compressor:
        """Get compressor instance by type."""
        return self._compressors[compression_type]

    def auto_select_compression(
        self,
        data: bytes,
        prefer_speed: bool = False,
        size_threshold: int = 1024
    ) -> CompressionType:
        """Automatically select best compression for given data."""
        # Don't compress small files
        if len(data) < size_threshold:
            return CompressionType.NONE

        # For very large files, prefer speed
        if len(data) > 100 * 1024 * 1024:  # 100MB
            return CompressionType.LZ4

        # Speed preference
        if prefer_speed:
            return CompressionType.LZ4

        # Default: balance of compression ratio and speed
        return CompressionType.GZIP

    def compress_with_stats(
        self,
        data: bytes,
        compression_type: CompressionType = None
    ) -> Tuple[bytes, CompressionType, float]:
        """Compress data and return compression stats."""
        if compression_type is None:
            compression_type = self.auto_select_compression(data)

        compressor = self.get_compressor(compression_type)
        compressed_data = compressor.compress(data)

        compression_ratio = len(compressed_data) / len(data) if data else 1.0

        return compressed_data, compression_type, compression_ratio

    def decompress_with_type(
        self,
        compressed_data: bytes,
        compression_type: CompressionType
    ) -> bytes:
        """Decompress data using specified compression type."""
        compressor = self.get_compressor(compression_type)
        return compressor.decompress(compressed_data)

    def detect_compression_type(self, data: bytes) -> CompressionType:
        """Attempt to detect compression type from data headers."""
        if not data:
            return CompressionType.NONE

        # GZIP magic number
        if data.startswith(b'\x1f\x8b'):
            return CompressionType.GZIP

        # LZ4 frame magic number
        if data.startswith(b'\x04"M\x18'):
            return CompressionType.LZ4

        # ZLIB magic numbers (RFC 1950)
        if len(data) >= 2:
            first_byte, second_byte = data[0], data[1]
            # Check for valid ZLIB header
            if (first_byte & 0x0F) == 8 and ((first_byte << 8) + second_byte) % 31 == 0:
                return CompressionType.ZLIB

        return CompressionType.NONE

    def get_recommended_extension(self, compression_type: CompressionType) -> str:
        """Get recommended file extension for compression type."""
        compressor = self.get_compressor(compression_type)
        return compressor.extension


# Global compression manager instance
_compression_manager = CompressionManager()


def get_compression_manager() -> CompressionManager:
    """Get the global compression manager instance."""
    return _compression_manager


def compress_data(
    data: bytes,
    compression_type: CompressionType = None,
    prefer_speed: bool = False
) -> Tuple[bytes, CompressionType, float]:
    """Convenience function to compress data with automatic type selection."""
    return _compression_manager.compress_with_stats(
        data,
        compression_type or _compression_manager.auto_select_compression(data, prefer_speed)
    )


def decompress_data(compressed_data: bytes, compression_type: CompressionType) -> bytes:
    """Convenience function to decompress data."""
    return _compression_manager.decompress_with_type(compressed_data, compression_type)


def detect_and_decompress(data: bytes) -> bytes:
    """Detect compression type and decompress if needed."""
    compression_type = _compression_manager.detect_compression_type(data)
    if compression_type == CompressionType.NONE:
        return data
    return decompress_data(data, compression_type)