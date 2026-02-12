"""
Camera Handler Module
=====================
Handles multiple camera sources: PC webcam, mobile camera, and CCTV/RTSP streams.
"""

import cv2
import numpy as np
from typing import Optional, Union

class CameraHandler:
    """Unified camera handler for multiple sources"""
    
    def __init__(self, source: Union[int, str] = 0):
        """
        Initialize camera handler
        
        Args:
            source: Camera source (0 for webcam, URL for RTSP/mobile)
        """
        self.source = source
        self.cap = None
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize camera capture"""
        try:
            # For RTSP or HTTP streams
            if isinstance(self.source, str):
                self.cap = cv2.VideoCapture(self.source)
            # For webcam (integer index)
            else:
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
        except Exception as e:
            raise Exception(f"Failed to initialize camera: {str(e)}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera
        
        Returns:
            Frame as numpy array or None if failed
        """
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        
        if not ret:
            return None
        
        return frame
    
    def release(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
    
    def is_opened(self) -> bool:
        """Check if camera is opened"""
        return self.cap is not None and self.cap.isOpened()
    
    @staticmethod
    def get_mobile_camera_url(ip: str, port: int = 8080) -> str:
        """
        Generate mobile camera URL (for IP Webcam app)
        
        Args:
            ip: Mobile device IP address
            port: Port number (default 8080)
            
        Returns:
            RTSP/HTTP URL for mobile camera
        """
        return f"http://{ip}:{port}/video"
    
    @staticmethod
    def get_rtsp_url(username: str, password: str, ip: str, port: int = 554, stream: str = "stream1") -> str:
        """
        Generate RTSP URL for CCTV cameras
        
        Args:
            username: Camera username
            password: Camera password
            ip: Camera IP address
            port: RTSP port (default 554)
            stream: Stream path
            
        Returns:
            RTSP URL
        """
        return f"rtsp://{username}:{password}@{ip}:{port}/{stream}"
