# Convalt

A Python library for converting between various image and audio formats with a simple, unified API.

## Features

- Single interface for all format conversions
- Support for popular image formats: PNG, JPEG, GIF, BMP, TIFF, WEBP, ICO
- Support for popular audio formats: MP3, WAV, OGG, FLAC, M4A, AAC
- Batch conversion capabilities
- Automatic handling of format-specific requirements
- Conversion history tracking
- Comprehensive error handling

## Installation

```bash
pip install convalt
```

For audio conversion support, you also need FFmpeg installed on your system:

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

## Quick Start

```python
from Convalt import Convalt

converter = Convalt()

# Convert image formats
converter.convert("input.png", "output.jpg", quality=90)

# Convert audio formats
converter.convert("song.mp3", "song.wav", bitrate="320k")

# Batch convert multiple files
files = ["image1.png", "image2.png", "image3.png"]
converter.batch_convert(files, "jpg", output_dir="converted")
```

## Usage Examples

### Basic Image Conversion

```python
from Convalt import Convalt

converter = Convalt()

# PNG to JPEG
converter.convert("photo.png", "photo.jpg", quality=95)

# JPEG to PNG
converter.convert("image.jpg", "image.png")

# PNG to GIF
converter.convert("animation.png", "animation.gif")
```

### Basic Audio Conversion

```python
# MP3 to WAV
converter.convert("song.mp3", "song.wav", bitrate="320k")

# WAV to MP3
converter.convert("audio.wav", "audio.mp3", bitrate="192k")

# MP3 to OGG
converter.convert("music.mp3", "music.ogg")
```

### Batch Conversion

```python
# Convert multiple images
image_files = ["photo1.png", "photo2.png", "photo3.png"]
converter.batch_convert(
    image_files, 
    "jpg", 
    output_dir="converted",
    quality=85
)

# Convert multiple audio files
audio_files = ["track1.mp3", "track2.mp3"]
converter.batch_convert(
    audio_files,
    "wav",
    output_dir="converted_audio"
)
```

### Advanced Options

```python
# High-quality JPEG with optimization
converter.convert(
    "original.png",
    "output.jpg",
    quality=98,
    optimize=True
)

# Optimized PNG
converter.convert(
    "large.png",
    "optimized.png",
    optimize=True
)

# High-bitrate audio
converter.convert(
    "source.wav",
    "output.mp3",
    bitrate="320k"
)
```

### Error Handling

```python
from Convalt import (
    Convalt, 
    ConversionError, 
    UnsupportedFormatError
)

converter = Convalt()

try:
    converter.convert("input.png", "output.jpg")
except FileNotFoundError:
    print("Input file not found")
except UnsupportedFormatError:
    print("Format conversion not supported")
except ConversionError as e:
    print(f"Conversion failed: {e}")
```

### Check Supported Formats

```python
converter = Convalt()
formats = converter.get_supported_formats()

print("Image formats:", formats['image'])
print("Audio formats:", formats['audio'])
```

### Conversion History

```python
converter = Convalt()

# Perform conversions
converter.convert("image1.png", "image1.jpg")
converter.convert("image2.png", "image2.jpg")

# View history
history = converter.get_history()
for item in history:
    print(f"{item['input_format']} → {item['output_format']}")
```

## API Reference

### Convalt

#### `convert(input_path, output_path, **kwargs)`

Convert a file from one format to another.

**Parameters:**
- `input_path` (str): Path to the input file
- `output_path` (str): Path to the output file
- `quality` (int): JPEG/WEBP quality, 1-100 (default: 95)
- `optimize` (bool): Optimize output file size (default: True)
- `bitrate` (str): Audio bitrate, e.g. "192k", "320k" (default: "192k")

**Returns:** Path to the converted file (str)

**Raises:**
- `FileNotFoundError`: Input file doesn't exist
- `UnsupportedFormatError`: Format conversion not supported
- `ConversionError`: Conversion failed

#### `batch_convert(input_files, output_format, output_dir=None, **kwargs)`

Convert multiple files to the same output format.

**Parameters:**
- `input_files` (list): List of input file paths
- `output_format` (str): Target format without dot (e.g., 'png', 'mp3')
- `output_dir` (str, optional): Output directory
- `**kwargs`: Additional conversion options

**Returns:** List of output file paths

#### `get_supported_formats()`

Get all supported formats by category.

**Returns:** Dictionary with 'image' and 'audio' keys containing lists of supported formats

#### `get_history()`

Get conversion history.

**Returns:** List of conversion records

## Supported Formats

### Image Formats
PNG, JPEG, JPG, GIF, BMP, TIFF, WEBP, ICO

### Audio Formats
MP3, WAV, OGG, FLAC, M4A, AAC

## Requirements

- Python 3.7+
- Pillow >= 10.0.0
- pydub >= 0.25.0
- FFmpeg (for audio conversion)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Pillow](https://python-pillow.org/) for image processing
- Built with [pydub](https://github.com/jiaaro/pydub) for audio processing
- Powered by [FFmpeg](https://ffmpeg.org/) for audio codec support

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.

## Changelog

### Version 1.0.0
- Initial release
- Image format conversion support
- Audio format conversion support
- Batch conversion capabilities
- Conversion history tracking