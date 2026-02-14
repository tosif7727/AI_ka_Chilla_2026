# ❌ MISTAKE: Remove this opening triple quote
"""
UI Components Module
====================
Reusable UI components for the Streamlit interface.
"""
# ✅ FIX: Keep the comment style but remove triple quotes, or use # for comments

# ✅ CORRECT: Use # for module header comments instead
# UI Components Module
# ====================
# Reusable UI components for the Streamlit interface.

import streamlit as st
import tempfile
import os
import time
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
        st.image("https://img.icons8.com/?size=100&id=l88MYrSg2nAT&format=png&color=000000 ", width=80)
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

            if st.button("➕ Add Channel", width='stretch):
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
        if st.button("🔔 Send Test Alert", width='content'):
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
    Render professional statistics dashboard with premium UI
    
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
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    # Status color logic
    if people_count == 0:
        status_color = "#3498db"
        status_text = "Active"
    elif people_count < 10:
        status_color = "#2ecc71"
        status_text = "Safe"
    elif people_count < 30:
        status_color = "#f39c12"
        status_text = "Crowded"
    else:
        status_color = "#e74c3c"
        status_text = "Critical"

    # Define CSS
    css = f"""
    <style>
        .stat-dashboard {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1rem;
            background: white;
            border-radius: 16px;
            padding: 1.2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid rgba(0,0,0,0.05);
            margin-bottom: 2rem;
            align-items: center;
        }}
        
        .stat-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 0 0.8rem;
            border-right: 1px solid #eee;
            transition: all 0.3s ease;
        }}
        
        .stat-item:last-child {{
            border-right: none;
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #7f8c8d;
            margin-bottom: 0.5rem;
            font-weight: 600;
            text-align: center;
            white-space: nowrap;
        }}
        
        .stat-value {{
            font-size: 1.8rem;
            font-weight: 800;
            color: #2c3e50;
            line-height: 1.2;
            font-family: 'Inter', sans-serif;
            text-align: center;
        }}
        
        .stat-icon {{
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            opacity: 0.8;
        }}
        
        .live-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: {status_color};
            box-shadow: 0 0 10px {status_color};
            animation: pulse-dot 2s infinite;
            margin-right: 8px;
            vertical-align: middle;
            margin-bottom: 4px;
        }}
        
        @keyframes pulse-dot {{
            0% {{ box-shadow: 0 0 0 0 {status_color}40; }}
            70% {{ box-shadow: 0 0 0 10px {status_color}00; }}
            100% {{ box-shadow: 0 0 0 0 {status_color}00; }}
        }}
        
        .stat-highlight {{
            color: {status_color};
        }}

        /* Responsive adjustments */
        @media (max-width: 900px) {{
            .stat-dashboard {{
                grid-template-columns: repeat(3, 1fr);
                gap: 1.5rem;
            }}
            .stat-item {{
                border-right: none;
                border-bottom: 1px solid #eee;
                padding-bottom: 1rem;
            }}
            .stat-item:nth-last-child(-n+2) {{
                border-bottom: none;
                padding-bottom: 0;
            }}
        }}
    </style>
    """

    # Define HTML content - Use a list to avoid indentation issues
    html_parts = [
        '<div class="stat-dashboard">',
        '    <div class="stat-item">',
        '        <div class="stat-icon">👥</div>',
        '        <div class="stat-label">Live Count</div>',
        f'        <div class="stat-value stat-highlight"><span class="live-indicator"></span>{people_count}</div>',
        '    </div>',
        '    <div class="stat-item">',
        '        <div class="stat-icon">📈</div>',
        '        <div class="stat-label">Peak Detected</div>',
        f'        <div class="stat-value">{st.session_state.max_count}</div>',
        '    </div>',
        '    <div class="stat-item">',
        '        <div class="stat-icon">⏱️</div>',
        '        <div class="stat-label">System Uptime</div>',
        f'        <div class="stat-value" style="font-size: 1.4rem;">{uptime_str}</div>',
        '    </div>',
        '    <div class="stat-item">',
        '        <div class="stat-icon">🛡️</div>',
        '        <div class="stat-label">Security Status</div>',
        f'        <div class="stat-value" style="font-size: 1.1rem; color: {status_color};">{status_text}</div>',
        '    </div>',
        '    <div class="stat-item">',
        '        <div class="stat-icon">⚡</div>',
        '        <div class="stat-label">Engine Mode</div>',
        f'        <div class="stat-value" style="font-size: 1.1rem;">{mode.split()[0]}</div>',
        '    </div>',
        '</div>'
    ]
    html_content = "\n".join(html_parts)
    
    # Render everything in one go
    st.markdown(css + html_content, unsafe_allow_html=True)


def render_alerts(alerts: List[Dict]):
    """
    Render professional alert notifications with premium animation
    
    Args:
        alerts: List of alert dictionaries
    """
    st.markdown("""
    <style>
        .alert-feed {
            max-height: 600px;
            overflow-y: auto;
            padding: 0.5rem;
            display: flex;
            flex-direction: column-reverse; /* Newest at top */
        }
        
        .alert-card {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border-left: 4px solid #ddd;
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .alert-card:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        
        .alert-card.warning {
            border-left-color: #ff4757;
            background: linear-gradient(to right, #fff 0%, #fff5f6 100%);
        }
        
        .alert-card.info {
            border-left-color: #2ed573;
            background: linear-gradient(to right, #fff 0%, #f0fff4 100%);
        }
        
        /* Pulse animation for the most recent alert */
        .alert-card:last-child {
            animation: slideIn 0.5s ease-out, glow 2s infinite;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes glow {
            0% { box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
            50% { box-shadow: 0 2px 15px rgba(255, 71, 87, 0.2); }
            100% { box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        }
        
        .alert-icon-box {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            flex-shrink: 0;
        }
        
        .warning .alert-icon-box {
            background: #ffe0e3;
            color: #ff4757;
        }
        
        .info .alert-icon-box {
            background: #dff9fb;
            color: #2ed573;
        }
        
        .alert-content {
            flex-grow: 1;
        }
        
        .alert-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.4rem;
        }
        
        .alert-title {
            font-weight: 700;
            font-size: 0.95rem;
            color: #2f3542;
        }
        
        .alert-time {
            font-size: 0.75rem;
            color: #a4b0be;
            font-family: monospace;
            background: #f1f2f6;
            padding: 2px 6px;
            border-radius: 4px;
        }
        
        .alert-message {
            font-size: 0.9rem;
            color: #57606f;
            line-height: 1.4;
        }
        
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #a4b0be;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if not alerts:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;">🛡️</div>
            <div style="font-weight: 600;">System Secure</div>
            <div style="font-size: 0.9rem;">No threats detected</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Show last 8 alerts
    recent_alerts = alerts[-8:]
    
    html = '<div class="alert-feed">'
    
    # We loop simply; the CSS flex-direction: column-reverse handles visual order if we dump them in order
    # BUT typically recent is top. CSS `column-reverse` puts the LAST element at the TOP.
    # So if we append alerts in chronological order (oldest -> newest), the last one (newest) will be at the top.
    
    for alert in recent_alerts:
        alert_type = alert.get('type', 'info')
        message = alert.get('message', 'Unknown event')
        timestamp = alert.get('time', '--:--')
        
        # Split message if it follows "[Source] Description" pattern
        if ']' in message:
            source, content = message.split(']', 1)
            source = source.strip('[').strip()
            content = content.strip()
        else:
            source = "System"
            content = message
            
        icon = "⚠️" if alert_type == 'warning' else "ℹ️"
        css_class = alert_type
        
        html += f"""
        <div class="alert-card {css_class}">
            <div class="alert-icon-box">{icon}</div>
            <div class="alert-content">
                <div class="alert-header">
                    <span class="alert-title">{source}</span>
                    <span class="alert-time">{timestamp}</span>
                </div>
                <div class="alert-message">{content}</div>
            </div>
        </div>
        """
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ❌ MISTAKE: Remove this closing triple quote - it was wrapping entire file
# """