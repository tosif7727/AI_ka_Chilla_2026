# People Counting (Camera & Video) — YOLOv8 👥

Overview
- This project uses YOLOv8 to detect and count people in a video stream (webcam) or from a video file. 📹
- Detections are drawn on frames and a CSV log of people count per frame is saved as `people_count_log.csv` 📝.

Requirements
- Python 3.8+
- Install required packages:
  - pip install ultralytics opencv-python pandas

Files
- main.py — runs detection and counting (switch between camera and video by changing the VideoCapture source). ▶️
- people_count_log.csv — generated after running; contains two columns: Frame, People_Count. 📊

How to run
1. Using a webcam:
   - In `main.py` set:
     - cap = cv2.VideoCapture(0)
   - Run:
     - python main.py

2. Using a video file:
   - In `main.py` set:
     - cap = cv2.VideoCapture("crowd.mp4")
   - Run:
     - python main.py

Behavior & Controls
- The script opens a window showing annotated frames and a running people count. 🖼️
- Press ESC to stop and close the window. ⎋
- After exit, `people_count_log.csv` is created in the working directory with one row per processed frame. ✅

Notes & Tips
- Ensure the YOLOv8 weights file exists (e.g., `yolov8n.pt`) or change the model path in `main.py`. ⚠️
- Adjust detection confidence by modifying `results = model(frame, conf=0.4)`. 🎯
- For better performance on longer videos or real-time camera streams, consider resizing frames before inference or using a GPU-enabled environment. ⚡

Troubleshooting
- If camera fails to open, try a different index (0, 1) or check camera permissions. 🔍
- If detections are poor, try a larger YOLO model or fine-tune thresholds. 🛠️

Social
- Kaggle 📊: https://www.kaggle.com/touseefafridi
- LinkedIn 💼: https://www.linkedin.com/in/touseef-afridi-35a59a250/
- GitHub 🐙: https://github.com/tosif7727

Replace the placeholder URLs above with your actual profile links. Optionally add badges or contact info here. ✉️
