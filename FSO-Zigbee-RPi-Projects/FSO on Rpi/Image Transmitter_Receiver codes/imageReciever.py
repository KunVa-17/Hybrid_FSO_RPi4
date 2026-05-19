from PIL import Image
import RPi.GPIO as GPIO
import time

# GPIO setup
GPIO.setmode(GPIO.BCM)
PHOTO_PIN = 18
GPIO.setup(PHOTO_PIN, GPIO.IN)

BIT_DURATION = 0.01  # Seconds

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
    wait_for_start()
    bits = ''
    for _ in range(8):
        time.sleep(BIT_DURATION)
        bits += read_bit()
    
    # Stop bits (ignored here but must be waited out)
    time.sleep(BIT_DURATION)
    time.sleep(BIT_DURATION)
    return int(bits, 2)

def sync_on_preamble():
    print("📡 Waiting for sync preamble...")
    count = 0
    while count < 10:
        byte = receive_byte()
        if byte == 0xAA:
            count += 1
        else:
            count = 0
    print("🔒 Sync established!")

def receive_image():
    sync_on_preamble()
    
    width = (receive_byte() << 8) + receive_byte()
    height = (receive_byte() << 8) + receive_byte()
    total_pixels = width * height

    print(f"🖼 Receiving image of size: {width}x{height}")
    bits_per_pixel = 12  # 8 data + 2 start + 2 stop
    eta = total_pixels * bits_per_pixel * BIT_DURATION
    print(f"Estimated time to complete: {eta:.1f} seconds\n")

    pixel_data = [0] * total_pixels
    img = Image.new('L', (width, height))

    last_update_time = time.time()

    for i in range(total_pixels):
        pixel_data[i] = receive_byte()

        # Live preview update
        if i % 100 == 0 or (time.time() - last_update_time) > 10:
            img.putdata(pixel_data)
            img.save("received_image_live.png")
            print(f"🟢 Updated preview at {i}/{total_pixels} pixels")
            last_update_time = time.time()

    # Save final image
    img.putdata(pixel_data)
    img.save("received_image.png")
    print("✅ Final image saved as 'received_image.png'")

try:
    receive_image()
finally:
    GPIO.cleanup()
