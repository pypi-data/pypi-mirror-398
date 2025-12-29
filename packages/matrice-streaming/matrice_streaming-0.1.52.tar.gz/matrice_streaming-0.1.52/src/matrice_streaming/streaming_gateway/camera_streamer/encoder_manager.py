"""Encoder management for video frame encoding."""
import logging
import numpy as np
from typing import Dict, Tuple, Optional, Any
from matrice_common.video import H265StreamEncoder, H265FrameEncoder


class EncoderConfig:
    """Configuration for encoding."""
    ENCODER_CHUNK_SIZE = 8192
    DEFAULT_QUALITY = 23


class EncoderManager:
    """Manages H.265 frame and stream encoders."""
    
    def __init__(self, h265_mode: str = "frame", quality: int = 23, use_hardware: bool = False):
        """Initialize encoder manager.
        
        Args:
            h265_mode: Encoding mode - "frame" or "stream"
            quality: H.265 quality (CRF value 0-51, lower=better)
            use_hardware: Use hardware encoding if available
        """
        self.h265_mode = h265_mode
        self.quality = quality
        self.use_hardware = use_hardware
        
        self.frame_encoders: Dict[str, H265FrameEncoder] = {}
        self.stream_encoders: Dict[str, H265StreamEncoder] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def encode_frame(
        self,
        frame: np.ndarray,
        stream_key: str,
        fps: int,
        width: int,
        height: int,
        metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any], str]:
        """Encode frame using configured mode.
        
        Args:
            frame: Frame to encode
            stream_key: Stream identifier
            fps: Frames per second
            width: Frame width
            height: Frame height
            metadata: Metadata dictionary to update
            
        Returns:
            Tuple of (encoded_data, updated_metadata, encoding_type)
        """
        try:
            if self.h265_mode == "frame":
                return self._encode_frame_wise(frame, stream_key, metadata)
            else:  # stream mode
                return self._encode_stream_wise(frame, stream_key, metadata, fps, width, height)
        except Exception as e:
            self.logger.error(f"H.265 encoding failed for stream {stream_key}: {e}")
            return frame.tobytes(), metadata, "raw_fallback"
    
    def cleanup(self):
        """Clean up all encoders."""
        # Close frame encoders
        for key, encoder in self.frame_encoders.items():
            try:
                if hasattr(encoder, 'close'):
                    encoder.close()
            except Exception as e:
                self.logger.warning(f"Failed to close frame encoder {key}: {e}")
        self.frame_encoders.clear()
        
        # Close stream encoders
        for key, encoder in self.stream_encoders.items():
            try:
                if hasattr(encoder, 'stop'):
                    encoder.stop()
                if hasattr(encoder, 'close'):
                    encoder.close()
            except Exception as e:
                self.logger.warning(f"Failed to close stream encoder {key}: {e}")
        self.stream_encoders.clear()
    
    # Private methods
    
    def _encode_frame_wise(
        self,
        frame: np.ndarray,
        stream_key: str,
        metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any], str]:
        """Encode single frame to H.265."""
        try:
            # Get or create frame encoder
            if stream_key not in self.frame_encoders:
                self.frame_encoders[stream_key] = H265FrameEncoder(
                    quality=self.quality,
                    use_hardware=self.use_hardware
                )
                self.logger.info(f"Created H.265 frame encoder for stream {stream_key}")
            
            encoder = self.frame_encoders[stream_key]
            h265_data = encoder.encode_frame(frame)
            
            if h265_data:
                metadata["encoding_type"] = "h265_frame"
                metadata["video_codec"] = "h265"
                metadata["compression_format"] = "hevc"
                return h265_data, metadata, "h265_frame"
            else:
                self.logger.warning(f"H.265 frame encoding failed for {stream_key}, using raw frame")
                return frame.tobytes(), metadata, "raw_fallback"
                
        except ImportError:
            self.logger.error("H.265 encoder not available, using raw frame")
            return frame.tobytes(), metadata, "raw_fallback"
        except Exception as e:
            self.logger.error(f"H.265 frame encoding error: {e}, using raw frame")
            return frame.tobytes(), metadata, "raw_fallback"
    
    def _encode_stream_wise(
        self,
        frame: np.ndarray,
        stream_key: str,
        metadata: Dict[str, Any],
        fps: int,
        width: int,
        height: int
    ) -> Tuple[bytes, Dict[str, Any], str]:
        """Encode frame using continuous H.265 stream."""
        try:
            # Get or create stream encoder
            if stream_key not in self.stream_encoders:
                encoder = H265StreamEncoder(
                    width=width, height=height, fps=fps,
                    quality=self.quality, use_hardware=self.use_hardware
                )
                
                if encoder.start():
                    self.stream_encoders[stream_key] = encoder
                    self.logger.info(f"Created H.265 stream encoder for {stream_key}: {width}x{height}@{fps}fps")
                else:
                    self.logger.error(f"Failed to start H.265 stream encoder for {stream_key}")
                    return frame.tobytes(), metadata, "raw_fallback"
            
            encoder = self.stream_encoders[stream_key]
            
            # Add frame to continuous stream
            if encoder.encode_frame(frame):
                # Try to read encoded bytes
                h265_chunk = encoder.read_bytes(chunk_size=EncoderConfig.ENCODER_CHUNK_SIZE)
                
                if h265_chunk:
                    metadata["encoding_type"] = "h265_stream_chunk"
                    metadata["video_codec"] = "h265"
                    metadata["compression_format"] = "hevc"
                    metadata["chunk_size"] = len(h265_chunk)
                    return h265_chunk, metadata, "h265_stream_chunk"
                else:
                    # Frame processed but no output ready yet
                    metadata["encoding_type"] = "h265_stream_buffered"
                    return b"", metadata, "h265_stream_buffered"
            else:
                self.logger.error(f"Failed to add frame to H.265 stream encoder for {stream_key}")
                return frame.tobytes(), metadata, "raw_fallback"
                
        except ImportError:
            self.logger.error("H.265 stream encoder not available, using raw frame")
            return frame.tobytes(), metadata, "raw_fallback"
        except Exception as e:
            self.logger.error(f"H.265 stream encoding error: {e}, using raw frame")
            return frame.tobytes(), metadata, "raw_fallback"

