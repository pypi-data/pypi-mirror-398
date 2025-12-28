from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
from pydub import AudioSegment


class ConversionError(Exception):
    """Raised when a conversion fails"""
    pass


class UnsupportedFormatError(Exception):
    """Raised when a format is not supported"""
    pass


class Convalt:
    """
    A universal format converter supporting image and audio formats.
    
    Supported image formats: PNG, JPEG, JPG, GIF, BMP, TIFF, WEBP, ICO
    Supported audio formats: MP3, WAV, OGG, FLAC, M4A, AAC, MP4
    """
    
    # Supported formats by category
    IMAGE_FORMATS = {'png', 'jpeg', 'jpg', 'gif', 'bmp', 'tiff', 'webp', 'ico'}
    AUDIO_FORMATS = {'mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'mp4'}
    
    def __init__(self):
        self.conversion_history = []
    
    def convert(
        self, 
        input_path: str, 
        output_path: str, 
        **kwargs
    ) -> str:
        """
        Convert a file from one format to another.
        
        Args:
            input_path: Path to the input file
            output_path: Path to the output file
            **kwargs: Additional conversion options (quality, bitrate, etc.)
            
        Returns:
            Path to the converted file
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            UnsupportedFormatError: If format is not supported
            ConversionError: If conversion fails
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Determine format types
        input_ext = input_path.suffix.lower().lstrip('.')
        output_ext = output_path.suffix.lower().lstrip('.')
        
        # Detect category
        if input_ext in self.IMAGE_FORMATS and output_ext in self.IMAGE_FORMATS:
            result = self._convert_image(input_path, output_path, **kwargs)
        elif input_ext in self.AUDIO_FORMATS and output_ext in self.AUDIO_FORMATS:
            result = self._convert_audio(input_path, output_path, **kwargs)
        else:
            raise UnsupportedFormatError(
                f"Conversion from {input_ext} to {output_ext} is not supported"
            )
        
        # Log conversion
        self.conversion_history.append({
            'input': str(input_path),
            'output': str(output_path),
            'input_format': input_ext,
            'output_format': output_ext
        })
        
        return result
    
    def _convert_image(
        self, 
        input_path: Path, 
        output_path: Path, 
        quality: int = 95,
        optimize: bool = True,
        **kwargs
    ) -> str:
        """
        Convert image formats using Pillow.
        
        Args:
            input_path: Path to input image
            output_path: Path to output image
            quality: JPEG quality (1-100), default 95
            optimize: Optimize output file size
            **kwargs: Additional Pillow save options
        """
        try:
            with Image.open(input_path) as img:
                # Handle transparency for formats that don't support it
                output_ext = output_path.suffix.lower().lstrip('.')
                
                if output_ext in ('jpg', 'jpeg') and img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG (no transparency)
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Prepare save options
                save_kwargs = {'optimize': optimize}
                
                if output_ext in ('jpg', 'jpeg'):
                    save_kwargs['quality'] = quality
                elif output_ext == 'png':
                    save_kwargs['compress_level'] = 9 if optimize else 6
                elif output_ext == 'webp':
                    save_kwargs['quality'] = quality
                
                # Merge with user-provided kwargs
                save_kwargs.update(kwargs)
                
                # Save the converted image
                img.save(output_path, **save_kwargs)
                
            return str(output_path)
            
        except Exception as e:
            raise ConversionError(f"Image conversion failed: {str(e)}")
    
    def _convert_audio(
        self, 
        input_path: Path, 
        output_path: Path,
        bitrate: str = "192k",
        **kwargs
    ) -> str:
        """
        Convert audio formats using pydub.
        
        Args:
            input_path: Path to input audio
            output_path: Path to output audio
            bitrate: Audio bitrate (e.g., "192k", "320k")
            **kwargs: Additional pydub export options
        """
        try:
            # Load audio file
            input_ext = input_path.suffix.lower().lstrip('.')
            audio = AudioSegment.from_file(input_path, format=input_ext)
            
            # Prepare export options
            output_ext = output_path.suffix.lower().lstrip('.')
            export_kwargs = {'format': output_ext, 'bitrate': bitrate}
            export_kwargs.update(kwargs)
            
            # Export to new format
            audio.export(output_path, **export_kwargs)
            
            return str(output_path)
            
        except Exception as e:
            raise ConversionError(f"Audio conversion failed: {str(e)}")
    
    def batch_convert(
        self, 
        input_files: list, 
        output_format: str,
        output_dir: Optional[str] = None,
        **kwargs
    ) -> list:
        """
        Convert multiple files to the same output format.
        
        Args:
            input_files: List of input file paths
            output_format: Target format (without dot, e.g., 'png', 'mp3')
            output_dir: Output directory (defaults to same as input)
            **kwargs: Conversion options
            
        Returns:
            List of output file paths
        """
        results = []
        
        for input_file in input_files:
            input_path = Path(input_file)
            
            if output_dir:
                output_path = Path(output_dir) / f"{input_path.stem}.{output_format}"
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path = input_path.parent / f"{input_path.stem}.{output_format}"
            
            try:
                result = self.convert(input_path, output_path, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Failed to convert {input_file}: {e}")
                results.append(None)
        
        return results
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get all supported formats by category."""
        return {
            'image': sorted(self.IMAGE_FORMATS),
            'audio': sorted(self.AUDIO_FORMATS)
        }
    
    def get_history(self) -> list:
        """Get conversion history."""
        return self.conversion_history.copy()


# Example usage
if __name__ == "__main__":
    converter = Convalt()
    
    # Print supported formats
    print("Supported formats:")
    formats = converter.get_supported_formats()
    print(f"Images: {', '.join(formats['image'])}")
    print(f"Audio: {', '.join(formats['audio'])}")
    print()
    
    # Example conversions (uncomment to test)
    
    # Image conversion
    # converter.convert("input.png", "output.jpg", quality=90)
    
    # Audio conversion
    # converter.convert("input.mp3", "output.wav", bitrate="320k")
    
    # Batch conversion
    # files = ["image1.png", "image2.png", "image3.png"]
    # converter.batch_convert(files, "jpg", output_dir="converted")
    
    print("Converter ready! Use the convert() method to convert files.")