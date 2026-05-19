import serial
import base64
import time
import os
from datetime import timedelta

PORT = '/dev/ttyUSB0'
BAUD = 9600
CHUNK_SIZE = 80

ser = serial.Serial(PORT, BAUD, timeout=1)

def send_image(filepath):
    with open(filepath, 'rb') as f:
        img_bytes = f.read()

    encoded = base64.b64encode(img_bytes).decode('ascii')
    total = len(encoded)
    print(f"[Image size: {len(img_bytes)/1024:.2f} KB | Encoded size: {total} bytes]")

    ser.write(b'START_IMAGE\n')
    time.sleep(0.1)

    start_time = time.time()
    for i in range(0, total, CHUNK_SIZE):
        chunk = encoded[i:i + CHUNK_SIZE]
        ser.write((chunk + '\n').encode('ascii'))
        time.sleep(0.005)  # slight delay to avoid buffer overflow

        # ⏳ Progress & ETA
        sent = i + CHUNK_SIZE
        percent = min(100, (sent / total) * 100)
        elapsed = time.time() - start_time
        speed = sent / elapsed
        eta = (total - sent) / speed if speed > 0 else 0
        print(f"\rProgress: {percent:.2f}% | ETA: {timedelta(seconds=int(eta))}", end='')

    ser.write(b'END_IMAGE\n')
    print("\n[Image sent]")

try:
    filepath = input("Enter path to image file to send: ").strip()
    assert os.path.isfile(filepath), "[!] File does not exist."
    send_image(filepath)
finally:
    ser.close()
