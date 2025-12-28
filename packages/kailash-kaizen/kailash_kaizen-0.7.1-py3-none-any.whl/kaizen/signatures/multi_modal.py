"""
Multi-modal signature fields for Kaizen.

This module provides ImageField and AudioField descriptors for multi-modal
signatures, enabling text + image + audio inputs for vision and audio models.

Supports:
- ImageField: File paths, URLs, base64, auto-resizing, format detection
- AudioField: File paths, format detection, duration extraction
- MultiModalSignature: Base class for mixed text/image/audio signatures

Example:
    >>> from kaizen.signatures.multi_modal import ImageField, MultiModalSignature
    >>> from kaizen.signatures import Signature, InputField, OutputField
    >>>
    >>> class VisionQASignature(MultiModalSignature, Signature):
    ...     image: ImageField = InputField(description="Image to analyze")
    ...     question: str = InputField(description="Question about image")
    ...     answer: str = OutputField(description="Answer")
"""

import base64
import io
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from PIL import Image
except ImportError:
    raise ImportError(
        "PIL (Pillow) is required for ImageField. "
        "Install it with: pip install Pillow"
    )

try:
    import requests
except ImportError:
    # Make requests optional for environments that don't need URL loading
    requests = None


@dataclass
class ImageField:
    """
    Image input field for multi-modal signatures.

    Supports:
    - File paths: "/path/to/image.png"
    - URLs: "https://example.com/image.jpg"
    - Base64: "data:image/jpeg;base64,..."
    - Auto-resizing for Ollama compatibility (max 2MB)
    - Format detection and validation

    Example:
        >>> from kaizen.signatures.multi_modal import ImageField
        >>> from kaizen.signatures import Signature, InputField
        >>>
        >>> class VisionSignature(Signature):
        ...     image: ImageField = InputField(
        ...         description="Image to analyze",
        ...         max_size_mb=2,
        ...         formats=["jpg", "png", "webp"]
        ...     )

    Attributes:
        description: Human-readable field description
        max_size_mb: Maximum image size in megabytes (default: 2.0)
        formats: Allowed image formats (default: jpg, jpeg, png, webp)
        auto_resize: Automatically resize large images (default: True)
        target_size: Target size for resizing (default: 768x768)
    """

    description: str = ""
    max_size_mb: float = 2.0
    formats: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png", "webp"])
    auto_resize: bool = True
    target_size: tuple = (768, 768)  # Ollama recommended size

    _data: Optional[bytes] = field(default=None, repr=False)
    _format: Optional[str] = field(default=None, repr=False)
    _size_bytes: int = field(default=0, repr=False)

    def load(self, source: Union[str, bytes, Path]) -> "ImageField":
        """
        Load image from various sources.

        Args:
            source: File path, URL, base64 string, or raw bytes

        Returns:
            Self for chaining

        Raises:
            FileNotFoundError: If file path doesn't exist
            ValueError: If base64 data is invalid or format unsupported
            RuntimeError: If URL loading fails

        Example:
            >>> field = ImageField()
            >>> field.load("/path/to/image.jpg")  # From file
            >>> field.load("https://example.com/image.png")  # From URL
            >>> field.load("data:image/jpeg;base64,...")  # From base64
        """
        if isinstance(source, (Path, str)):
            source_str = str(source)

            # Check if URL
            if source_str.startswith(("http://", "https://")):
                self._load_from_url(source_str)
            # Check if base64
            elif source_str.startswith("data:image"):
                self._load_from_base64(source_str)
            # Assume file path
            else:
                self._load_from_file(source_str)
        elif isinstance(source, bytes):
            self._data = source
            self._size_bytes = len(source)
            self._detect_format()
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

        # Auto-resize if needed
        if self.auto_resize and self._size_bytes > self.max_size_mb * 1024 * 1024:
            self._resize_image()

        return self

    def _load_from_file(self, file_path: str):
        """Load image from file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        with open(file_path, "rb") as f:
            self._data = f.read()

        self._size_bytes = len(self._data)
        self._detect_format()

    def _load_from_url(self, url: str):
        """Load image from URL."""
        if requests is None:
            raise ImportError(
                "requests library is required for URL loading. "
                "Install it with: pip install requests"
            )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self._data = response.content
            self._size_bytes = len(self._data)
            self._detect_format()
        except Exception as e:
            raise RuntimeError(f"Failed to load image from URL: {e}")

    def _load_from_base64(self, base64_str: str):
        """Load image from base64 string."""
        try:
            # Remove data URL prefix if present
            if "," in base64_str:
                base64_str = base64_str.split(",", 1)[1]

            self._data = base64.b64decode(base64_str)
            self._size_bytes = len(self._data)
            self._detect_format()
        except Exception as e:
            raise ValueError(f"Invalid base64 image data: {e}")

    def _detect_format(self):
        """Detect image format from data."""
        if not self._data:
            return

        try:
            with Image.open(io.BytesIO(self._data)) as img:
                self._format = img.format.lower()
        except Exception as e:
            raise ValueError(f"Invalid image data: {e}")

        # Validate format
        if self._format not in self.formats:
            raise ValueError(
                f"Unsupported image format: {self._format}. "
                f"Supported: {self.formats}"
            )

    def _resize_image(self):
        """Resize image to target size."""
        try:
            with Image.open(io.BytesIO(self._data)) as img:
                # Maintain aspect ratio
                img.thumbnail(self.target_size, Image.Resampling.LANCZOS)

                # Convert to RGB if needed (Ollama compatibility)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Save to bytes
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85, optimize=True)
                self._data = buffer.getvalue()
                self._size_bytes = len(self._data)
                self._format = "jpeg"
        except Exception as e:
            raise RuntimeError(f"Failed to resize image: {e}")

    def to_base64(self) -> str:
        """
        Convert image to base64 string.

        Returns:
            Base64-encoded image with data URL prefix

        Raises:
            ValueError: If no image data is loaded

        Example:
            >>> field = ImageField()
            >>> field.load("image.jpg")
            >>> b64 = field.to_base64()
            >>> print(b64[:50])  # data:image/jpeg;base64,/9j/4AAQSkZJRg...
        """
        if not self._data:
            raise ValueError("No image data loaded")

        b64_str = base64.b64encode(self._data).decode("utf-8")
        return f"data:image/{self._format};base64,{b64_str}"

    def validate(self) -> bool:
        """
        Validate image field has valid data.

        Returns:
            True if image is valid, False otherwise

        Checks:
        - Image data is loaded
        - Format is supported
        - Size is within limits

        Example:
            >>> field = ImageField()
            >>> field.load("image.jpg")
            >>> if field.validate():
            ...     print("Image is valid")
        """
        return (
            self._data is not None
            and self._format in self.formats
            and self._size_bytes <= self.max_size_mb * 1024 * 1024
        )


@dataclass
class AudioField:
    """
    Audio input field for multi-modal signatures.

    Supports:
    - File paths: "/path/to/audio.mp3"
    - Format detection: MP3, WAV, M4A, OGG
    - Duration extraction (with pydub if available)

    Example:
        >>> from kaizen.signatures.multi_modal import AudioField
        >>> from kaizen.signatures import Signature, InputField
        >>>
        >>> class TranscriptionSignature(Signature):
        ...     audio: AudioField = InputField(
        ...         description="Audio to transcribe",
        ...         max_duration_sec=600,  # 10 minutes
        ...         formats=["mp3", "wav", "m4a"]
        ...     )

    Attributes:
        description: Human-readable field description
        max_duration_sec: Maximum audio duration in seconds (default: 600)
        max_size_mb: Maximum audio size in megabytes (default: 25.0)
        formats: Allowed audio formats (default: mp3, wav, m4a, ogg)
    """

    description: str = ""
    max_duration_sec: float = 600.0  # 10 minutes
    max_size_mb: float = 25.0
    formats: List[str] = field(default_factory=lambda: ["mp3", "wav", "m4a", "ogg"])

    _data: Optional[bytes] = field(default=None, repr=False)
    _format: Optional[str] = field(default=None, repr=False)
    _size_bytes: int = field(default=0, repr=False)
    _duration_sec: float = field(default=0.0, repr=False)

    def load(self, source: Union[str, bytes, Path]) -> "AudioField":
        """
        Load audio from file path.

        Args:
            source: File path or raw bytes

        Returns:
            Self for chaining

        Raises:
            FileNotFoundError: If file path doesn't exist
            ValueError: If format is unsupported

        Example:
            >>> field = AudioField()
            >>> field.load("/path/to/audio.mp3")
        """
        if isinstance(source, (Path, str)):
            self._load_from_file(str(source))
        elif isinstance(source, bytes):
            self._data = source
            self._size_bytes = len(source)
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

        return self

    def _load_from_file(self, file_path: str):
        """Load audio from file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        with open(file_path, "rb") as f:
            self._data = f.read()

        self._size_bytes = len(self._data)
        self._detect_format(file_path)
        self._extract_duration(file_path)

    def _detect_format(self, file_path: str):
        """Detect audio format from file extension."""
        ext = Path(file_path).suffix.lstrip(".").lower()

        if ext not in self.formats:
            raise ValueError(
                f"Unsupported audio format: {ext}. " f"Supported: {self.formats}"
            )

        self._format = ext

    def _extract_duration(self, file_path: str):
        """Extract audio duration using pydub or fallback estimation."""
        try:
            # Try with pydub if available
            from pydub import AudioSegment

            audio = AudioSegment.from_file(file_path)
            self._duration_sec = len(audio) / 1000.0  # milliseconds to seconds
        except ImportError:
            # Fallback: estimate from file size (rough approximation)
            # Assume 128 kbps MP3
            self._duration_sec = self._size_bytes / (128 * 1024 / 8)

    def validate(self) -> bool:
        """
        Validate audio field has valid data.

        Returns:
            True if audio is valid, False otherwise

        Checks:
        - Audio data is loaded
        - Format is supported
        - Size is within limits
        - Duration is within limits

        Example:
            >>> field = AudioField()
            >>> field.load("audio.mp3")
            >>> if field.validate():
            ...     print("Audio is valid")
        """
        return (
            self._data is not None
            and self._format in self.formats
            and self._size_bytes <= self.max_size_mb * 1024 * 1024
            and self._duration_sec <= self.max_duration_sec
        )


class MultiModalSignature:
    """
    Base class for multi-modal signatures.

    Extends regular Signature to support:
    - ImageField inputs
    - AudioField inputs
    - Mixed text/image/audio fields
    - Auto-formatting for Ollama vision API

    Example:
        >>> from kaizen.signatures import Signature, InputField, OutputField
        >>> from kaizen.signatures.multi_modal import (
        ...     MultiModalSignature, ImageField
        ... )
        >>>
        >>> class VisionQASignature(MultiModalSignature, Signature):
        ...     image: ImageField = InputField(description="Image to analyze")
        ...     question: str = InputField(description="Question about image")
        ...     answer: str = OutputField(description="Answer")
        >>>
        >>> # Format inputs for Ollama
        >>> sig = VisionQASignature()
        >>> image = ImageField().load("photo.jpg")
        >>> formatted = sig.format_for_ollama(
        ...     image=image,
        ...     question="What's in this photo?"
        ... )
        >>> print(formatted.keys())  # dict_keys(['content', 'images'])
    """

    @classmethod
    def format_for_ollama(cls, **inputs) -> Dict[str, Any]:
        """
        Format inputs for Ollama vision API.

        Args:
            **inputs: Signature input values (text, ImageField, AudioField)

        Returns:
            Dict with 'content' (text) and optional 'images' (base64) for Ollama

        Example:
            >>> image = ImageField().load("photo.jpg")
            >>> result = MultiModalSignature.format_for_ollama(
            ...     image=image,
            ...     question="What is this?"
            ... )
            >>> print(result['content'])  # question: What is this?
            >>> print(len(result['images']))  # 1
        """
        text_parts = []
        images = []

        for field_name, value in inputs.items():
            if isinstance(value, ImageField):
                # Add image as base64
                if value._data:
                    images.append(value.to_base64())
            elif isinstance(value, str):
                text_parts.append(f"{field_name}: {value}")

        result = {"content": " ".join(text_parts)}

        if images:
            result["images"] = images

        return result
