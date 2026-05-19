import base64
from PIL import Image
import RPi.GPIO as GPIO
import time
import serial
import threading
from datetime import timedelta

# === GPIO & Serial Setup ===
PORT = '/dev/ttyUSB0'
BAUD = 9600
ser = serial.Serial(PORT, BAUD, timeout=1)

GPIO.setmode(GPIO.BCM)
LASER_PIN = 23
GPIO.setup(LASER_PIN, GPIO.OUT)

BIT_DURATION = 0.01
IMAGE_PATH = "new.jpg"
CHUNK_SIZE = 128  # Tune this based on serial buffer size

# === FSO Sending Functions ===
def send_bit(bit):
    GPIO.output(LASER_PIN, GPIO.HIGH if bit == '0' else GPIO.LOW)
    time.sleep(BIT_DURATION)

def send_byte(byte):
    binary = format(byte, '08b')
    send_bit('1')
    send_bit('1')
    for b in binary:
        send_bit(b)
    send_bit('0')
    send_bit('0')

def send_sync_preamble():
    for _ in range(10):
        send_byte(0xAA)

def send_image_fso(img):
    width, height = img.size
    pixels = list(img.getdata())

    # Send header
    for value in [width >> 8, width & 0xFF, height >> 8, height & 0xFF]:
        send_byte(value)

    # Send pixels
    for pixel in pixels:
        send_byte(pixel)

def transmit_fso():
    img = Image.open(IMAGE_PATH).resize((64, 64))
    mode_flag = 0x03 if img.mode == 'RGB' else 0x01

    if mode_flag == 0x01:
        img = img.convert('L')
        pixels = list(img.getdata())  # 1 byte/pixel
    else:
        img = img.convert('RGB')
        pixels = list(img.getdata())  # 3 bytes/pixel

    width, height = img.size
    print(f"🔦 Transmitting image via FSO: {img.size} | Mode: {'RGB' if mode_flag==0x03 else 'Grayscale'}")
    
    send_sync_preamble()

    # === Send header ===
    header = [
        mode_flag,                # 1 byte: format
        width >> 8, width & 0xFF, # 2 bytes: width
        height >> 8, height & 0xFF # 2 bytes: height
    ]
    for value in header:
        send_byte(value)

    # === Send pixels ===
    for pixel in pixels:
        if mode_flag == 0x01:
            send_byte(pixel)
        else:
            r, g, b = pixel
            send_byte(r)
            send_byte(g)
            send_byte(b)

    print("✅ FSO transmission complete")

# === Zigbee Transmission ===
def send_image_zigbee(filepath):
    with open(filepath, 'rb') as f:
        img_bytes = f.read()
        encoded = base64.b64encode(img_bytes).decode('ascii')
        total = len(encoded)

    print(f"[Zigbee Image: {len(img_bytes)/1024:.2f} KB | Encoded size: {total} bytes]")
    ser.write(b'START_IMAGE\n')
    time.sleep(0.1)
    start_time = time.time()

    for i in range(0, total, CHUNK_SIZE):
        chunk = encoded[i:i + CHUNK_SIZE]
        ser.write((chunk + '\n').encode('ascii'))
        time.sleep(0.005)

        # Progress & ETA
        sent = i + CHUNK_SIZE
        percent = min(100, (sent / total) * 100)
        elapsed = time.time() - start_time
        speed = sent / elapsed
        eta = (total - sent) / speed if speed > 0 else 0
        print(f"\r📡 Zigbee Progress: {percent:.2f}% | ETA: {timedelta(seconds=int(eta))}", end='')

    ser.write(b'END_IMAGE\n')
    print("\n✅ Image sent over Zigbee")

# === Zigbee Listener ===
def listen_for_zigbee_requests():
    while True:
        line = ser.readline().decode().strip()
        if line == "REQ_IMAGE":
            print("\n📨 Zigbee request received. Sending image...")
            send_image_zigbee(IMAGE_PATH)

# === MAIN ===
try:
    zigbee_thread = threading.Thread(target=listen_for_zigbee_requests, daemon=True)
    zigbee_thread.start()

    print("⏳ Waiting 3 seconds before FSO transmission...")
    time.sleep(3)
    transmit_fso()

    print("📡 Listening for Zigbee fallback requests...")
    while True:
        time.sleep(1)

finally:
    GPIO.cleanup()
    ser.close()
