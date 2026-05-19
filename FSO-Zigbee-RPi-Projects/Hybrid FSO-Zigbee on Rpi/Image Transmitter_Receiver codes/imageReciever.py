import RPi.GPIO as GPIO
import serial
import time
from PIL import Image
import base64
from io import BytesIO
from datetime import datetime

# === CONFIG ===
PHOTO_PIN = 18
ZIGBEE_PORT = '/dev/ttyUSB0'
BAUD = 9600

BIT_DURATION = 0.01
BYTE_TIMEOUT = 0.05
LINK_TIMEOUT = 2.0

GPIO.setmode(GPIO.BCM)
GPIO.setup(PHOTO_PIN, GPIO.IN)

def read_bit():
    return '0' if GPIO.input(PHOTO_PIN) == GPIO.LOW else '1'

def wait_for_start():
    while True:
        if read_bit() == '1':
            time.sleep(BIT_DURATION)
            if read_bit() == '1':
                return
        time.sleep(BIT_DURATION / 2)

def receive_byte():
    while read_bit() != '1':
        time.sleep(BIT_DURATION / 4)
    time.sleep(BIT_DURATION)
    if read_bit() != '1':
        raise ValueError("Framing error")

    bits = ''
    for _ in range(8):
        time.sleep(BIT_DURATION)
        bits += read_bit()

    time.sleep(BIT_DURATION)
    if read_bit() != '0':
        raise ValueError("Framing error")
    time.sleep(BIT_DURATION)
    if read_bit() != '0':
        raise ValueError("Framing error")

    return int(bits, 2)

def safe_receive_byte(timeout=BYTE_TIMEOUT):
    start_time = time.time()
    while True:
        try:
            return receive_byte()
        except ValueError:
            if time.time() - start_time > timeout:
                return None

def sync_on_preamble():
    print("📡 Waiting for sync preamble...")
    count = 0
    while count < 10:
        byte = safe_receive_byte()
        if byte == 0xAA:
            count += 1
        else:
            count = 0

def receive_image_fso():
    sync_on_preamble()
    print("🔒 Sync established!")

    # === Receive header: [mode, width_hi, width_lo, height_hi, height_lo]
    header_bytes = []
    for _ in range(5):
        byte = safe_receive_byte()
        if byte is None:
            print("⚠️ Header timeout!")
            return None
        header_bytes.append(byte)

    mode_flag = header_bytes[0]
    width = (header_bytes[1] << 8) + header_bytes[2]
    height = (header_bytes[3] << 8) + header_bytes[4]
    total_pixels = width * height

    if mode_flag == 0x01:
        mode = 'L'
        bytes_per_pixel = 1
    elif mode_flag == 0x03:
        mode = 'RGB'
        bytes_per_pixel = 3
    else:
        print(f"❌ Unknown image mode flag: {mode_flag}")
        return None

    print(f"📥 Receiving {mode} image: {width}x{height} ({total_pixels} pixels)")

    pixel_data = []
    img = Image.new(mode, (width, height))
    last_update = time.time()
    last_byte_time = time.time()

    for i in range(total_pixels):
        pixel = []
        for _ in range(bytes_per_pixel):
            byte = safe_receive_byte()
            if byte is not None:
                pixel.append(byte)
                last_byte_time = time.time()
            else:
                if time.time() - last_byte_time > LINK_TIMEOUT:
                    print(f"⚠️ Link broken at pixel {i}! Switching to Zigbee...")
                    return "zigbee"

        if mode == 'L':
            pixel_data.append(pixel[0])
        else:
            # Validate RGB pixel
            if len(pixel) == 3:
                pixel_data.append(tuple(pixel))
            else:
                pixel_data.append((0, 0, 0))  # fallback for malformed pixel

        # Periodic live preview update
        if i % 100 == 0 or (time.time() - last_update > 5):
            preview = []

            if mode == 'L':
                for p in pixel_data:
                    preview.append(int(p) if p is not None else 0)
                preview.extend([0] * (total_pixels - len(preview)))
            else:
                for p in pixel_data:
                    if isinstance(p, (list, tuple)) and len(p) == 3:
                        preview.append(tuple(map(int, p)))
                    else:
                        preview.append((0, 0, 0))
                preview.extend([(0, 0, 0)] * (total_pixels - len(preview)))

            try:
                img.putdata(preview)
                img.save("received_image_live_fso.png")
            except Exception as e:
                print(f"❌ Preview update failed: {e}")

            progress = len(pixel_data) / total_pixels * 100
            print(f"🟢 Progress: {len(pixel_data)}/{total_pixels} ({progress:.1f}%)")
            last_update = time.time()

    img.putdata(pixel_data)
    img.save("received_image_fso.png")
    print("✅ RGB image saved as 'received_image_fso.png'")
    return "done"

def request_image_over_zigbee():
    print("📡 Requesting image over Zigbee...")
    with serial.Serial(ZIGBEE_PORT, BAUD, timeout=2) as zig:
        zig.write(b'REQ_IMAGE\n')

        buffer = ""
        in_image = False
        start_time = time.time()

        while True:
            line = zig.readline().decode(errors='ignore').strip()
            if not line:
                if time.time() - start_time > 10:
                    print("❌ Zigbee response timeout.")
                    return
                continue

            if line == "START_IMAGE":
                in_image = True
                buffer = ""
                print("📡 Zigbee transmission started...")
                continue
            elif line == "END_IMAGE":
                print("📦 Zigbee image received. Decoding...")
                break
            elif in_image:
                buffer += line
                print(f"\r📥 Zigbee Bytes: {len(buffer)}", end='')

        try:
            decoded_bytes = base64.b64decode(buffer)
            image = Image.open(BytesIO(decoded_bytes)).convert("RGB")
            image.save("received_image_zigbee.png")
            print("\n✅ Zigbee RGB image saved.")
        except Exception as e:
            print(f"\n❌ Failed to decode Zigbee image: {e}")

# === MAIN ===
try:
    while True:
        result = receive_image_fso()
        if result == "zigbee":
            request_image_over_zigbee()
        elif result == "done":
            break
        else:
            print("🔁 Retrying FSO...")
            time.sleep(1)
finally:
    GPIO.cleanup()
