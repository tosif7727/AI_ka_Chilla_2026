from ultralytics import YOLO
import cv2
import pandas as pd

# Load YOLOv8 model (ensure yolov8n.pt is available or update path)
model = YOLO("yolov8n.pt")

# Video source:
# - Uncomment the camera line to use a live webcam
# - Use the file path to process a saved video
#live video feed from camera
# cap = cv2.VideoCapture(0)
#video from file
cap = cv2.VideoCapture("crowd.mp4")

# Counters and storage for logging results per frame
frame_count = 0
log_data = []

# Main processing loop: read frames, run inference, count people, display and log
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Run model inference on the current frame (conf threshold adjustable)
    results = model(frame, conf=0.4)
    annotated = results[0].plot()  # annotated frame returned by ultralytics

    # Count detected persons in this frame
    people_count = 0

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]

        if class_name == "person":
            people_count += 1

    # Increment frame counter and add an entry for CSV logging
    frame_count += 1
    log_data.append([frame_count, people_count])

    # Overlay people count on the annotated frame (emoji may depend on platform fonts)
    cv2.putText(
        annotated,
        f"👥 People: {people_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    # Display annotated frame in a window (title includes emoji)
    cv2.imshow("People Counting & Object Detection — 👥", annotated)

    # Lightweight console log per frame
    print(f"Frame {frame_count}: {people_count} 👥")

    # Exit on ESC key
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Cleanup resources
cap.release()
cv2.destroyAllWindows()

# Persist log to CSV (columns: Frame, People_Count)
df = pd.DataFrame(log_data, columns=["Frame", "People_Count"])
df.to_csv("people_count_log.csv", index=False)
