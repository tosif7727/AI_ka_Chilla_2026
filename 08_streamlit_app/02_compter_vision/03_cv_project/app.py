"""
Security Vision System - Main Application (Live Video Version)
==========================================
A comprehensive computer vision system for people counting and suspicious action detection.
Supports multiple camera sources: PC webcam, mobile, and CCTV cameras.
"""

import streamlit as st
import cv2
import numpy as np
from pathlib import Path
import sys
import time

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.camera_handler import CameraHandler
from utils.detector import PeopleDetector, ActionDetector
from utils.ui_components import render_sidebar, render_stats, render_alerts
from utils.overlay import draw_warning_overlay, draw_blinking_border

# Page Configuration
st.set_page_config(
    page_title="Security Vision System",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
    }
    
    .alert-box {
        background: #ff4b4b15;
        border-left: 4px solid #ff4b4b;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #00cc0015;
        border-left: 4px solid #00cc00;
        padding: 1rem;
        border-radius: 10px;
    }
    
    .count-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        animation: pulse 2s ease-in-out infinite;
    }
    
    .count-number {
        font-size: 4rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .count-label {
        font-size: 1.5rem;
        font-weight: 300;
        margin: 0;
        opacity: 0.9;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    .warning-banner {
        background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%);
        padding: 2.5rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 24px rgba(255, 0, 0, 0.4);
        animation: blink 1s ease-in-out infinite, shake 0.5s ease-in-out infinite;
        border: 4px solid #ffffff;
    }
    
    .warning-icon {
        font-size: 5rem;
        margin-bottom: 1rem;
        animation: rotate 2s linear infinite;
    }
    
    .warning-title {
        font-size: 3.5rem;
        font-weight: 900;
        margin: 1rem 0;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
        letter-spacing: 2px;
    }
    
    .warning-subtitle {
        font-size: 1.8rem;
        font-weight: 400;
        margin: 0.5rem 0;
        opacity: 0.95;
    }
    
    @keyframes blink {
        0%, 49%, 100% { opacity: 1; }
        50%, 99% { opacity: 0.7; }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'total_count' not in st.session_state:
        st.session_state.total_count = 0
    if 'alerts' not in st.session_state:
        st.session_state.alerts = []
    if 'detector' not in st.session_state or not hasattr(st.session_state.detector, 'annotate_people'):
        # Load detector once in session state (or reload if stale)
        with st.spinner("🔄 Loading Base AI model..."):
            st.session_state.detector = PeopleDetector()
            
    if 'action_detector' not in st.session_state or not hasattr(st.session_state.action_detector, 'annotate_actions'):
        with st.spinner("🔄 Loading Action AI model..."):
            st.session_state.action_detector = ActionDetector()
    if 'cameras' not in st.session_state:
        st.session_state.cameras = {} # {cam_id: CameraHandler}
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False
    if 'last_alert_time' not in st.session_state:
        st.session_state.last_alert_time = {} # {action_type: timestamp}

def main():
    """Main application function"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎥 Security Vision System v2.0</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    camera_list, detection_mode, confidence, sensitivity = render_sidebar()
    
    # Update detection settings
    st.session_state.detector.confidence_threshold = confidence
    st.session_state.action_detector.confidence_threshold = confidence
    st.session_state.action_detector.sensitivity = sensitivity
    
    # Statistics Header
    stats_placeholder = st.empty()

    # Main area
    col_main, col_side = st.columns([3, 1])
    
    with col_main:
        # Control Buttons
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("🎬 Start All Active", use_container_width=True, type="primary"):
                st.session_state.camera_active = True
        with c2:
            if st.button("⏹️ Stop All", use_container_width=True):
                st.session_state.camera_active = False
                for cam in st.session_state.cameras.values():
                    cam.release()
                st.session_state.cameras = {}
        
        # Video Grid
        active_cams = [c for c in camera_list if c.get('active', False)]
        if not active_cams:
            st.info("💡 Add and enable a camera channel in the sidebar to begin.")
            st.session_state.camera_active = False
        
        placeholders = {}
        if active_cams:
            n_cols = 2 if len(active_cams) > 1 else 1
            grid_cols = st.columns(n_cols)
            for i, cam in enumerate(active_cams):
                with grid_cols[i % n_cols]:
                    st.caption(f"📺 {cam['name']}")
                    placeholders[i] = st.empty()

    with col_side:
        st.subheader("🚨 Recent Alerts")
        alerts_placeholder = st.empty()

    # Streaming Loop
    if st.session_state.camera_active:
        # Initialize handlers
        for i, cam_cfg in enumerate(active_cams):
            if i not in st.session_state.cameras:
                try:
                    st.session_state.cameras[i] = CameraHandler(cam_cfg['source'])
                except Exception as e:
                    st.error(f"Failed to connect to {cam_cfg['name']}")

        # Initialize persistence for frame skipping
        if 'frame_count' not in st.session_state:
            st.session_state.frame_count = 0
        if 'last_results' not in st.session_state:
            st.session_state.last_results = {} # {cam_idx: {'people': [], 'actions': [], 'action_res': None}}

        while st.session_state.camera_active:
            current_total_count = 0
            st.session_state.frame_count += 1
            
            # Run detection every 3 frames to prevent lag
            run_detection = (st.session_state.frame_count % 3 == 0)
            
            for i, cam_cfg in enumerate(active_cams):
                if i not in st.session_state.cameras: continue
                
                frame = st.session_state.cameras[i].get_frame()
                if frame is None: continue
                
                # Initialize result storage for this camera if needed
                if i not in st.session_state.last_results:
                    st.session_state.last_results[i] = {'people': [], 'actions': [], 'action_res': None}
                
                processed_frame = frame.copy()
                cam_count = 0
                
                # --- DETECTION PHASE ---
                if run_detection:
                    # People Detection
                    if detection_mode in ["People Counting", "Both"]:
                        people_boxes = st.session_state.detector.predict_people(frame)
                        st.session_state.last_results[i]['people'] = people_boxes
                        cam_count = len(people_boxes)
                    
                    # Action Detection
                    if detection_mode in ["Suspicious Actions", "Both"]:
                        actions, action_res = st.session_state.action_detector.predict_actions(frame)
                        st.session_state.last_results[i]['actions'] = actions
                        st.session_state.last_results[i]['action_res'] = action_res
                        
                        # Alert Logic (only run when we detect new things)
                        current_time = time.time()
                        for action in actions:
                            action_key = f"{cam_cfg['name']}_{action['type']}"
                            is_new_action = action_key not in st.session_state.last_alert_time or (current_time - st.session_state.last_alert_time[action_key] > 10)
                            
                            if is_new_action:
                                alert_msg = f"[{cam_cfg['name']}] {action['description']}"
                                recent_msgs = [a['message'] for a in st.session_state.alerts[-5:]]
                                if alert_msg not in recent_msgs:
                                    st.session_state.alerts.append({
                                        'type': 'warning',
                                        'message': alert_msg,
                                        'time': time.strftime("%H:%M:%S")
                                    })
                                    if len(st.session_state.alerts) > 100:
                                        st.session_state.alerts = st.session_state.alerts[-100:]
                                    st.session_state.last_alert_time[action_key] = current_time

                # --- DRAWING PHASE (Always run using last known results) ---
                # Draw People
                if detection_mode in ["People Counting", "Both"]:
                    people_boxes = st.session_state.last_results[i]['people']
                    processed_frame = st.session_state.detector.annotate_people(processed_frame, people_boxes)
                    cam_count = len(people_boxes)
                    current_total_count += cam_count
                
                # Draw Actions
                if detection_mode in ["Suspicious Actions", "Both"]:
                    actions = st.session_state.last_results[i]['actions']
                    action_res = st.session_state.last_results[i]['action_res']
                    processed_frame = st.session_state.action_detector.annotate_actions(processed_frame, actions, action_res)
                    
                    # Draw Warning Overlay for high confidence actions
                    if actions:
                        # Prioritize most critical action
                        primary_action = actions[0]
                        processed_frame = draw_warning_overlay(
                            processed_frame, 
                            primary_action['type'], 
                            primary_action['description']
                        )
                
                # Update Video
                placeholders[i].image(processed_frame, channels="BGR", use_container_width=True)
            
            st.session_state.total_count = current_total_count
            
            # Update Stats & Alerts
            with stats_placeholder:
                render_stats(st.session_state.total_count, detection_mode)
            with alerts_placeholder:
                render_alerts(st.session_state.alerts)
            
            # Small sleep to yield to UI thread, but keep it minimal
            time.sleep(0.001)

    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #666;'>Security Vision System v2.0 | Multi-Channel Support</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
