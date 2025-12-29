"""Video capture management with robust retry logic."""
import logging
import time
import cv2
import requests
import os
import tempfile
import hashlib
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from typing import Union, Optional, Tuple, Dict, Any


class VideoSourceConfig:
    """Configuration for video source handling."""
    MAX_CAPTURE_RETRIES = 3
    CAPTURE_RETRY_DELAY = 2.0
    MAX_CONSECUTIVE_FAILURES = 10
    DOWNLOAD_TIMEOUT = 30
    DOWNLOAD_CHUNK_SIZE = 8192
    DEFAULT_BUFFER_SIZE = 5  # Increased from 1 to 5 for better throughput
    DEFAULT_FPS = 30


class VideoCaptureManager:
    """Manages video capture from various sources with retry logic and caching.
    
    Features URL deduplication: if multiple cameras use the same video URL
    (ignoring query parameters like AWS signed URL tokens), the video is only
    downloaded once and the local path is shared between cameras.
    """
    
    def __init__(self):
        """Initialize video capture manager."""
        # Maps full URL -> local file path (for backwards compatibility)
        self.downloaded_files: Dict[str, str] = {}
        # Maps normalized URL (without query params) -> local file path (for deduplication)
        self._normalized_url_to_path: Dict[str, str] = {}
        self.temp_dir = Path(tempfile.gettempdir()) / "matrice_streaming_cache"
        self.temp_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def prepare_source(self, source: Union[str, int], stream_key: str) -> Union[str, int]:
        """Prepare video source, downloading if it's a URL.
        
        Args:
            source: Video source (camera index, file path, or URL)
            stream_key: Stream identifier for caching
            
        Returns:
            Prepared source (downloaded file path or original source)
        """
        if isinstance(source, str) and self._is_downloadable_url(source):
            local_path = self._download_video_file(source, stream_key)
            if local_path:
                self.logger.debug(f"Using downloaded file: {local_path}")
                return local_path
            else:
                self.logger.warning(f"Failed to download {source}, will try to use URL directly")
        return source
    
    def open_capture(
        self,
        source: Union[str, int],
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Tuple[cv2.VideoCapture, str]:
        """Open video capture with retry logic.
        
        Args:
            source: Video source
            width: Target width for camera
            height: Target height for camera
            
        Returns:
            Tuple of (VideoCapture object, source_type)
            
        Raises:
            RuntimeError: If unable to open capture after retries
        """
        for attempt in range(VideoSourceConfig.MAX_CAPTURE_RETRIES):
            try:
                source_type = self._detect_source_type(source)
                cap = cv2.VideoCapture(self._get_capture_source(source))
                
                if not cap.isOpened():
                    raise RuntimeError(f"Failed to open source: {source}")
                
                self._configure_capture(cap, source_type, width, height)
                
                self.logger.info(f"Opened {source_type} source: {source}")
                return cap, source_type
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1}/{VideoSourceConfig.MAX_CAPTURE_RETRIES} failed: {e}")
                if attempt < VideoSourceConfig.MAX_CAPTURE_RETRIES - 1:
                    time.sleep(VideoSourceConfig.CAPTURE_RETRY_DELAY)
                else:
                    raise RuntimeError(f"Failed to open source after {VideoSourceConfig.MAX_CAPTURE_RETRIES} attempts")
    
    def get_video_properties(self, cap: cv2.VideoCapture) -> Dict[str, Any]:
        """Extract video properties from capture.
        
        Args:
            cap: VideoCapture object
            
        Returns:
            Dictionary with video properties
        """
        return {
            "original_fps": float(cap.get(cv2.CAP_PROP_FPS) or VideoSourceConfig.DEFAULT_FPS),
            "frame_count": cap.get(cv2.CAP_PROP_FRAME_COUNT),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }
    
    def calculate_frame_skip(self, source_type: str, original_fps: float, target_fps: int) -> int:
        """Calculate frame skip rate for RTSP streams.
        
        Args:
            source_type: Type of video source
            original_fps: Original FPS from video
            target_fps: Target FPS for streaming
            
        Returns:
            Frame skip rate (1 means no skip)
        """
        if source_type == "rtsp" and original_fps > target_fps:
            frame_skip = max(1, int(original_fps / target_fps))
            self.logger.info(f"RTSP frame skip: {frame_skip} (original: {original_fps}, target: {target_fps})")
            return frame_skip
        return 1
    
    def cleanup(self):
        """Clean up downloaded temporary files."""
        # Collect unique file paths (since multiple URLs may point to the same file)
        unique_files = set(self.downloaded_files.values())
        unique_files.update(self._normalized_url_to_path.values())
        
        for filepath in unique_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self.logger.debug(f"Removed temp file: {filepath}")
            except Exception as e:
                self.logger.warning(f"Failed to remove temp file {filepath}: {e}")
        
        self.downloaded_files.clear()
        self._normalized_url_to_path.clear()
    
    # Private methods
    
    def _is_downloadable_url(self, source: str) -> bool:
        """Check if source is a downloadable URL (not RTSP)."""
        return (source.startswith('http://') or source.startswith('https://')) and not source.startswith('rtsp')
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by stripping query parameters.
        
        This allows URLs that point to the same file but have different
        query parameters (e.g., AWS signed URLs with different tokens)
        to be recognized as the same resource.
        
        Args:
            url: Full URL with potential query parameters
            
        Returns:
            Normalized URL without query parameters
        """
        parsed = urlparse(url)
        # Rebuild URL without query string and fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            '',  # params
            '',  # query
            ''   # fragment
        ))
        return normalized
    
    def _get_url_hash(self, normalized_url: str) -> str:
        """Generate a short hash for the normalized URL.
        
        This is used for creating unique but consistent file names.
        
        Args:
            normalized_url: URL without query parameters
            
        Returns:
            Short hash string
        """
        return hashlib.md5(normalized_url.encode()).hexdigest()[:12]
    
    def _download_video_file(self, url: str, stream_key: str) -> Optional[str]:
        """Download video file from URL and cache it locally.
        
        Uses URL deduplication: if the same video (by normalized URL without 
        query parameters) has already been downloaded, returns the existing 
        local path instead of downloading again.
        
        Args:
            url: Video file URL (may include query parameters like AWS signatures)
            stream_key: Stream identifier
            
        Returns:
            Local file path or None if download failed
        """
        try:
            # Normalize URL to check for duplicate downloads
            # (same file but different query params, e.g., different AWS signatures)
            normalized_url = self._normalize_url(url)
            
            # Generate a consistent filename using URL hash
            file_ext = Path(url.split('?')[0]).suffix or '.mp4'
            url_hash = self._get_url_hash(normalized_url)
            expected_path = self.temp_dir / f"video_{url_hash}{file_ext}"
            expected_path_str = str(expected_path)
            
            # Quick check: if file already exists on disk, use it
            if os.path.exists(expected_path):
                self.logger.debug(
                    f"Reusing existing video file for {stream_key}: {expected_path} "
                    f"(already downloaded)"
                )
                # Update caches
                self.downloaded_files[url] = expected_path_str
                self._normalized_url_to_path[normalized_url] = expected_path_str
                return expected_path_str
            
            # Check memory cache for exact URL
            if url in self.downloaded_files:
                local_path = self.downloaded_files[url]
                if os.path.exists(local_path):
                    self.logger.debug(f"Using cached video file (exact URL match): {local_path}")
                    return local_path
            
            # Check memory cache for normalized URL
            if normalized_url in self._normalized_url_to_path:
                local_path = self._normalized_url_to_path[normalized_url]
                if os.path.exists(local_path):
                    self.logger.debug(
                        f"Reusing previously downloaded file for {stream_key}: {local_path} "
                        f"(same base URL, different query params)"
                    )
                    self.downloaded_files[url] = local_path
                    return local_path
            
            # Download the file
            self.logger.info(f"Downloading video file from: {url}")
            response = requests.get(url, stream=True, timeout=VideoSourceConfig.DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            
            with open(expected_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=VideoSourceConfig.DOWNLOAD_CHUNK_SIZE):
                    f.write(chunk)
            
            # Cache for both exact URL and normalized URL
            self.downloaded_files[url] = expected_path_str
            self._normalized_url_to_path[normalized_url] = expected_path_str
            
            self.logger.info(f"Downloaded video file to: {expected_path}")
            return expected_path_str
            
        except Exception as e:
            self.logger.error(f"Failed to download video file: {e}")
            return None
    
    def _detect_source_type(self, source: Union[str, int]) -> str:
        """Detect the type of video source."""
        if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
            return "camera"
        elif isinstance(source, str) and source.startswith("rtsp"):
            return "rtsp"
        elif isinstance(source, str) and source.startswith("http"):
            return "http"
        else:
            return "video_file"
    
    def _get_capture_source(self, source: Union[str, int]) -> Union[str, int]:
        """Get the actual source to pass to cv2.VideoCapture."""
        if isinstance(source, str) and source.isdigit():
            return int(source)
        return source
    
    def _configure_capture(
        self,
        cap: cv2.VideoCapture,
        source_type: str,
        width: Optional[int],
        height: Optional[int]
    ):
        """Configure capture settings based on source type."""
        if source_type in ["camera", "rtsp"]:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, VideoSourceConfig.DEFAULT_BUFFER_SIZE)
        
        if source_type == "camera":
            if width:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            if height:
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

