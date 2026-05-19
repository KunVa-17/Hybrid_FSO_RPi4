import serial
import base64
from PIL import Image
from io import BytesIO
import os

PORT = '/dev/ttyUSB0'
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)

def live_preview(b64_data, temp_path='temp.jpg'):
    try:
        img_bytes = base64.b64decode(b64_data)
        img = Image.open(BytesIO(img_bytes))
        img.save(temp_path)
        os.system(f"feh --auto-zoom --reload 1 {temp_path} &> /dev/null &")
    except:
        pass  # ignore until we have enough image data

def receive_image(save_path='received_image.jpg'):
    receiving = False
    b64_data = []

    print("[Waiting for image data...]")

    while True:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if not line:
            continue

        if line == 'START_IMAGE':
            print("[Image transfer started]")
            receiving = True
            b64_data.clear()

        elif line == 'END_IMAGE':
            print("[Image transfer ended]")
            full_b64 = ''.join(b64_data)
            try:
                img_bytes = base64.b64decode(full_b64)
                with open(save_path, 'wb') as f:
                    f.write(img_bytes)
                print(f"[Image saved to {save_path}]")
            except Exception as e:
                print(f"[Error decoding image: {e}]")
            break

        elif receiving:
            b64_data.append(line)
            if len(b64_data) % 15 == 0:  # update live every 15 chunks
                live_preview(''.join(b64_data))

try:
    receive_image()
finally:
    ser.close()
