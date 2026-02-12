"""
UI Components Module
====================
Reusable UI components for the Streamlit interface.
"""

import streamlit as st
import tempfile
import os
from typing import List, Dict

def render_sidebar() -> tuple:
    """
    Render sidebar with configuration options
    
    Returns:
        Tuple of (camera_list, detection_mode, confidence, sensitivity)
    """
    if 'camera_list' not in st.session_state:
        st.session_state.camera_list = []
    
    with st.sidebar:
        st.image("https://img.icons8.com/?size=100&id=l88MYrSg2nAT&format=png&color=000000", width=80)
        st.title("⚙️ Configuration")
        
        st.markdown("---")
        
        # Camera Source Selection
        st.subheader("📹 Manage Channels")
        
        with st.expander("➕ Add New Camera", expanded=not st.session_state.camera_list):
            camera_type = st.radio(
                "Select Camera Type:",
                ["PC Webcam", "Mobile Camera", "CCTV/RTSP", "Video File"],
                help="Choose your camera source"
            )
            
            new_source = None
            source_name = st.text_input("Channel Name", placeholder="Main Entrance")
            
            if camera_type == "PC Webcam":
                camera_index = st.number_input("Camera Index", min_value=0, max_value=5, value=0)
                new_source = camera_index
                
            elif camera_type == "Mobile Camera":
                mobile_ip = st.text_input("Mobile IP Address", placeholder="192.168.1.100")
                mobile_port = st.number_input("Port", value=8080)
                if mobile_ip:
                    new_source = f"http://{mobile_ip}:{mobile_port}/video"
            
            elif camera_type == "CCTV/RTSP":
                rtsp_url = st.text_input("RTSP URL", placeholder="rtsp://...", type="password")
                if rtsp_url:
                    new_source = rtsp_url
            
            else:  # Video File
                uploaded_file = st.file_uploader("Choose a video...", type=["mp4", "avi", "mov", "mkv"])
                if uploaded_file:
                    suffix = os.path.splitext(uploaded_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
                        tfile.write(uploaded_file.read())
                        new_source = tfile.name
                        if not source_name:
                            source_name = uploaded_file.name

            if st.button("➕ Add Channel", use_container_width=True):
                if new_source is not None:
                    name = source_name if source_name else f"Cam {len(st.session_state.camera_list) + 1}"
                    st.session_state.camera_list.append({"name": name, "source": new_source, "active": True})
                    st.success(f"Added {name}")
                    st.rerun()
                else:
                    st.error("Please configure source correctly")

        if st.session_state.camera_list:
            st.markdown("#### Current Channels")
            for i, cam in enumerate(st.session_state.camera_list):
                col_name, col_del = st.columns([4, 1])
                with col_name:
                    cam['active'] = st.checkbox(f"{cam['name']}", value=cam.get('active', True), key=f"cam_{i}")
                with col_del:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.camera_list.pop(i)
                        st.rerun()
        
        st.markdown("---")
        
        # Detection Mode
        st.subheader("🎯 Detection Mode")
        detection_mode = st.selectbox(
            "Select Mode:",
            ["People Counting", "Suspicious Actions", "Both"],
            help="Choose what to detect"
        )
        
        st.markdown("---")
        
        # Model Settings
        st.subheader("🔧 Model Settings")
        confidence = st.slider(
            "Confidence Threshold",
            min_value=0.1, max_value=1.0, value=0.4, step=0.05,
            help="Lower = more detections but more false positives"
        )
        
        sensitivity = st.select_slider(
            "Action Sensitivity",
            options=["Low", "Medium", "High"],
            value="Medium",
            help="How strictly to flag suspicious movements"
        )
        
        st.markdown("---")
        
        # Alert Settings
        st.subheader("🚨 Alert Settings")
        enable_alerts = st.checkbox("Enable Notifications", value=True)
        
        if enable_alerts:
            st.info("Alerts will appear in the dashboard side-panel.")
        
        st.markdown("---")
        
        # Developer Tools
        st.markdown("---")
        st.subheader("🛠️ Developer Tools")
        if st.button("🔔 Send Test Alert", use_container_width=True):
            if 'alerts' not in st.session_state:
                st.session_state.alerts = []
            st.session_state.alerts.append({
                'type': 'info',
                'message': "Test: System is monitoring correctly",
                'time': time.strftime("%H:%M:%S")
            })
            st.toast("✅ Test alert sent to dashboard!")
        
        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Security Vision System v2.0**
            - Multi-Camera Support
            - Action Detection (Optimized)
            - Real-time Alerts
            """)
    
    return st.session_state.camera_list, detection_mode, confidence, sensitivity


def render_stats(people_count: int, mode: str):
    """
    Render professional statistics dashboard
    
    Args:
        people_count: Current people count
        mode: Detection mode
    """
    import streamlit as st
    from datetime import datetime
    
    # Initialize session state for statistics
    if 'max_count' not in st.session_state:
        st.session_state.max_count = 0
    if 'total_detected' not in st.session_state:
        st.session_state.total_detected = 0
    if 'start_time' not in st.session_state:
        st.session_state.start_time = datetime.now()
    
    # Update statistics
    if people_count > st.session_state.max_count:
        st.session_state.max_count = people_count
    st.session_state.total_detected += people_count
    
    # Calculate uptime
    uptime = datetime.now() - st.session_state.start_time
    uptime_str = f"{uptime.seconds // 60}m {uptime.seconds % 60}s"
    
    # Status color
    if people_count == 0:
        status_color = "#3498db"  # Blue
        status_icon = "🔵"
        status_text = "Monitoring"
    elif people_count < 10:
        status_color = "#2ecc71"  # Green
        status_icon = "🟢"
        status_text = "Normal"
    elif people_count < 30:
        status_color = "#f39c12"  # Orange
        status_icon = "🟡"
        status_text = "Moderate"
    else:
        status_color = "#e74c3c"  # Red
        status_icon = "🔴"
        status_text = "High Traffic"
    
    # Render modern stats cards
    st.markdown(f"""
    <style>
        .metric-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid {status_color};
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: {status_color};
            margin: 0.5rem 0;
            line-height: 1;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        
        .metric-icon {{
            font-size: 2rem;
            float: right;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            background: {status_color}15;
            color: {status_color};
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        
        .mini-metric {{
            background: #f8f9fa;
            padding: 0.8rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .mini-metric-label {{
            font-size: 0.85rem;
            color: #666;
        }}
        
        .mini-metric-value {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #333;
        }}
    </style>
    
    <div class="metric-card">
        <div class="metric-icon">{status_icon}</div>
        <div class="metric-label">Current Count</div>
        <div class="metric-value">{people_count}</div>
        <div class="status-badge">{status_icon} {status_text}</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-icon">📊</div>
        <div class="metric-label">Peak Count</div>
        <div class="metric-value">{st.session_state.max_count}</div>
    </div>
    
    <div class="mini-metric">
        <span class="mini-metric-label">⏱️ Uptime</span>
        <span class="mini-metric-value">{uptime_str}</span>
    </div>
    
    <div class="mini-metric">
        <span class="mini-metric-label">🎯 Mode</span>
        <span class="mini-metric-value">{mode}</span>
    </div>
    
    <div class="mini-metric">
        <span class="mini-metric-label">🤖 Engine</span>
        <span class="mini-metric-value">YOLOv8</span>
    </div>
    """, unsafe_allow_html=True)


def render_alerts(alerts: List[Dict]):
    """
    Render professional alert notifications
    
    Args:
        alerts: List of alert dictionaries
    """
    st.markdown("""
    <style>
        .alert-container {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .alert-item {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }
        
        .alert-item.success {
            background: #d4edda;
            border-left-color: #28a745;
        }
        
        .alert-icon {
            font-size: 1.5rem;
        }
        
        .alert-text {
            flex: 1;
            font-size: 0.9rem;
            color: #333;
            font-weight: 500;
        }
        
        .no-alerts {
            text-align: center;
            padding: 2rem 1rem;
            color: #28a745;
        }
        
        .no-alerts-icon {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        
        .no-alerts-text {
            font-size: 1.1rem;
            font-weight: 600;
            color: #28a745;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if not alerts:
        st.markdown("""
        <div class="alert-container">
            <div class="no-alerts">
                <div class="no-alerts-icon">✅</div>
                <div class="no-alerts-text">All Clear</div>
                <div style="color: #666; font-size: 0.85rem; margin-top: 0.5rem;">
                    No alerts detected
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Show last 5 alerts
    recent_alerts = alerts[-5:]
    
    alerts_html = '<div class="alert-container">'
    
    for alert in reversed(recent_alerts):
        alert_type = alert.get('type', 'info')
        message = alert.get('message', 'Unknown alert')
        
        if alert_type == 'warning':
            icon = '⚠️'
            css_class = 'alert-item'
        else:
            icon = '🔔'
            css_class = 'alert-item'
        
        timestamp = alert.get('time', '')
        alerts_html += f"""
        <div class="{css_class}">
            <div class="alert-icon">{icon}</div>
            <div class="alert-text">
                <span style="color: #888; font-size: 0.75rem;">[{timestamp}]</span><br>
                {message}
            </div>
        </div>
        """
    
    alerts_html += '</div>'
    
    st.markdown(alerts_html, unsafe_allow_html=True)
