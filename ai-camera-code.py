import cv2
import numpy as np
import serial
import serial.tools.list_ports
import time

# 🔎 Auto-detect ESP32 COM port
def find_esp32_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Silicon Labs" in port.description or "CP210x" in port.description:
            return port.device
    return None

esp_port = find_esp32_port()
if esp_port is None:
    print("❌ ESP32 not found. Plug it in and try again.")
    exit()

print(f"✅ Connected to ESP32 on {esp_port}")
esp = serial.Serial(esp_port, 9600, timeout=2)
time.sleep(2)

cap = cv2.VideoCapture(0)

last_angle = 90  # Neutral

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        break

    frame = cv2.resize(frame, (640, 480))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:
                x, y, w, h = cv2.boundingRect(cnt)
                center_x = x + w // 2

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                cv2.putText(frame, "LOCKED", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                angle = int((center_x / 640) * 180)

                # ✅ Only send if different
                if angle != last_angle:
                    esp.write(f"{angle}\n".encode())
                    print(f"Sending angle: {angle}")
                    last_angle = angle
                break
    else:
        # ✅ No light → keep neutral 90
        if last_angle != 90:
            esp.write(b"90\n")
            print("No target → Sending neutral 90")
            last_angle = 90

    cv2.imshow("Missile Guidance View", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
esp.close()
