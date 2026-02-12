# 🎥 Security Vision System v2.0

<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/touseef-afridi-35a59a250/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/tosif7727)

**A professional-grade computer vision surveillance system featuring real-time people counting, multi-channel camera support, and AI-powered suspicious action detection.**

[Features](#✨-key-features) • [Installation](#🚀-installation) • [Usage Guide](#💻-usage-guide) • [Multi-Camera Support](#📹-multi-camera-management) • [AI Capabilities](#🎯-ai-capabilities)

</div>

---

## 📋 Project Overview

The **Security Vision System** is a modular, high-performance monitoring solution designed for modern security needs. Unlike traditional CCTV systems, it leverages **Deep Learning (YOLOv8 & Pose Estimation)** to not just record video, but to understand what is happening in real-time.

Version 2.0 introduces **Multi-Channel Management**, allowing security personnel to monitor multiple locations simultaneously through a single centralized dashboard.

---

## ✨ Key Features

- **📹 Multi-Channel Video Grid**: Add, name, and monitor multiple camera streams in a responsive grid layout.
- **👥 Dynamic People Counting**: Real-time tracking and counting of individuals across all active channels.
- **🚨 Suspicious Action Detection**:
  - **Falling Detection**: Alerts when a person falls or is lying on the ground.
  - **Aggressive Stances**: Detects fighting poses or aggressive arm movements.
  - **Threat Detection**: Flags "Hands Up" (surrender/robbery) gestures.
  - **Crouching/Hiding**: Identifies individuals attempting to hide or crouch.
- **🔔 Intelligent Alert Dashboard**:
  - Centralized alert panel with channel-specific tags (e.g., `[Front Desk] Fall detected`).
  - **Smart Cooldowns**: Prevents notification flooding by deduplicating and spacing out alerts.
- **🔧 Action Sensitivity Control**: Adjustable sensitivity (Low, Medium, High) to tune detection for different environments.
- **💻 Multi-Source Support**: Connect to Webcams, Mobile Cameras (IP Webcam), RTSP/CCTV streams, and Video Files for testing.
- **🛠️ Developer Tools**: Built-in "Send Test Alert" feature to verify system health instantly.

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Windows 10/11, Linux, or MacOS

### Setup Steps

1. **Clone & Navigate**

   ```bash
   cd d:\ai_work\08_streamlit_app\02_compter_vision\03_cv_project
   ```

2. **Initialize Environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Usage Guide

### 1. Launch the Application

```bash
streamlit run app.py
```

### 2. Configure Your Security Grid

1. Use the **Sidebar** to add your first "Channel".
2. Select your source (e.g., "PC Webcam" or "Video File").
3. Give your channel a name (e.g., "Main Entrance").
4. Click **Add Channel**. Repeat this for multiple cameras.

### 3. Choose Detection Mode

- **People Counting**: Focuses on crowd tracking and capacity monitoring.
- **Suspicious Actions**: Highlights only individuals performing doubtful actions in red.
- **Both**: Comprehensive monitoring for both count and security events.

### 4. Start Monitoring

Click the **🎬 Start All Active** button to begin the live AI processing for all your channels.

---

## 📹 Multi-Camera Management

The system supports a variety of sources to fit any infrastructure:

- **PC Webcam**: Use local USB cameras.
- **Mobile Camera**: Use apps like "IP Webcam" to turn any Android/iOS device into a security camera.
- **CCTV/RTSP**: Connect to professional IP cameras using standard RTSP URLs.
- **Video File**: Upload `.mp4` or `.avi` files to test the AI performance on recorded footage.

---

## 🎯 AI Capabilities

| Action Type           | Description                                                              | Alert Severity |
| --------------------- | ------------------------------------------------------------------------ | -------------- |
| **Fall Detected**     | Triggered when a person's head moves significantly below shoulder level. | 🔴 High        |
| **Hands Up**          | Triggered when both hands are raised above the head (Possible threat).   | 🔴 High        |
| **Aggressive Stance** | Detects arms extended or raised in a guarding/fighting posture.          | 🔴 High        |
| **Crouching**         | Detects persons hiding or crouching low to the ground.                   | 🟡 Medium      |
| **People Count**      | Real-time headcount displayed in the channel header and dashboard.       | 🔵 Info        |

---

## 📁 Project Structure

```text
03_cv_project/
├── app.py                  # Core Logic & Streamlit Entry Point
├── utils/
│   ├── detector.py         # AI Logic (YOLO & Pose Estimation)
│   ├── camera_handler.py   # Multi-source Stream Management
│   ├── ui_components.py    # Sidebar, Stats, and Dashboard UI
│   └── overlay.py          # Visual Drawing Utilities
├── yolov8n.pt              # People Detection Model
├── yolov8n-pose.pt         # Action Detection Model
└── README.md               # Documentation
```

---

## 🛠️ Technical Stack

- **Framework**: Streamlit
- **CV Engine**: OpenCV (4.9.0+)
- **AI Models**: Ultralytics YOLOv8 (Nano & Pose variants)
- **Programming**: Python 3.8+

---

<div align="center">

**Built for Security Professionals & Vision Enthusiasts**
_Security Vision System v2.0_

</div>
