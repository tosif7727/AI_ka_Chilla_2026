"""
UI Overlay Module
=================
Create visual overlays for video frames
"""

import cv2
import numpy as np

def draw_warning_overlay(frame: np.ndarray, action_type: str, description: str, severity: str = 'high') -> np.ndarray:
    """
    Draw a big warning overlay on the video frame
    
    Args:
        frame: Input video frame
        action_type: Type of action detected
        description: Action description
        severity: Severity level (high/medium)
        
    Returns:
        Frame with warning overlay
    """
    height, width = frame.shape[:2]
    overlay = frame.copy()
    
    # Create semi-transparent red background
    if severity == 'high':
        color = (0, 0, 255)  # Red for high severity
        bg_color = (0, 0, 200)
    else:
        color = (0, 165, 255)  # Orange for medium severity
        bg_color = (0, 140, 200)
    
    # Calculate overlay dimensions (centered, 80% width, 40% height)
    overlay_width = int(width * 0.8)
    overlay_height = int(height * 0.4)
    x_start = (width - overlay_width) // 2
    y_start = (height - overlay_height) // 2
    x_end = x_start + overlay_width
    y_end = y_start + overlay_height
    
    # Draw semi-transparent background
    cv2.rectangle(overlay, (x_start, y_start), (x_end, y_end), bg_color, -1)
    
    # Blend with original frame for transparency
    alpha = 0.85  # Transparency level
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    
    # Draw white border
    cv2.rectangle(frame, (x_start, y_start), (x_end, y_end), (255, 255, 255), 8)
    
    # Draw warning icon (triangle)
    icon_size = 80
    icon_center_x = width // 2
    icon_y = y_start + 60
    
    # Triangle points
    pt1 = (icon_center_x, icon_y - icon_size)
    pt2 = (icon_center_x - icon_size, icon_y + icon_size)
    pt3 = (icon_center_x + icon_size, icon_y + icon_size)
    
    # Draw filled triangle
    triangle_cnt = np.array([pt1, pt2, pt3])
    cv2.drawContours(frame, [triangle_cnt], 0, (0, 255, 255), -1)  # Yellow fill
    cv2.drawContours(frame, [triangle_cnt], 0, (255, 255, 255), 4)  # White border
    
    # Draw exclamation mark in triangle
    cv2.putText(frame, "!", (icon_center_x - 20, icon_y + 30), 
                cv2.FONT_HERSHEY_TRIPLEX, 3, (0, 0, 0), 8)
    
    # Draw "ALERT" text
    alert_text = "ALERT!"
    text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_TRIPLEX, 2.5, 6)[0]
    text_x = (width - text_size[0]) // 2
    text_y = icon_y + icon_size + 80
    
    # Draw text with shadow
    cv2.putText(frame, alert_text, (text_x + 4, text_y + 4), 
                cv2.FONT_HERSHEY_TRIPLEX, 2.5, (0, 0, 0), 6)  # Shadow
    cv2.putText(frame, alert_text, (text_x, text_y), 
                cv2.FONT_HERSHEY_TRIPLEX, 2.5, (255, 255, 255), 6)  # White text
    
    # Draw action type
    action_display = action_type.replace('_', ' ').upper()
    text_size = cv2.getTextSize(action_display, cv2.FONT_HERSHEY_TRIPLEX, 1.8, 4)[0]
    text_x = (width - text_size[0]) // 2
    text_y = text_y + 70
    
    cv2.putText(frame, action_display, (text_x + 3, text_y + 3), 
                cv2.FONT_HERSHEY_TRIPLEX, 1.8, (0, 0, 0), 4)  # Shadow
    cv2.putText(frame, action_display, (text_x, text_y), 
                cv2.FONT_HERSHEY_TRIPLEX, 1.8, (0, 255, 255), 4)  # Yellow text
    
    # Draw description (split into multiple lines if needed)
    words = description.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        text_size = cv2.getTextSize(test_line, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
        
        if text_size[0] > overlay_width - 40:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw description lines
    desc_y = text_y + 60
    for line in lines[:3]:  # Max 3 lines
        text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
        text_x = (width - text_size[0]) // 2
        
        cv2.putText(frame, line, (text_x + 2, desc_y + 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)  # Shadow
        cv2.putText(frame, line, (text_x, desc_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)  # White text
        desc_y += 40
    
    return frame


def draw_blinking_border(frame: np.ndarray, color: tuple = (0, 0, 255), thickness: int = 10) -> np.ndarray:
    """
    Draw a blinking border around the frame
    
    Args:
        frame: Input video frame
        color: Border color (BGR)
        thickness: Border thickness
        
    Returns:
        Frame with border
    """
    height, width = frame.shape[:2]
    
    # Draw border
    cv2.rectangle(frame, (0, 0), (width-1, height-1), color, thickness)
    
    return frame
