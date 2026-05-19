from PIL import Image
import RPi.GPIO as GPIO
import time

# GPIO setup
GPIO.setmode(GPIO.BCM)
LASER_PIN = 23
GPIO.setup(LASER_PIN, GPIO.OUT)

BIT_DURATION = 0.01  # Adjust for speed
IMAGE_PATH = "new.jpg"

time.sleep(5)
print("Starting transmission...")

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

def send_image(img):
    width, height = img.size
    pixels = list(img.getdata())
    
    # Send header (2 bytes width, 2 bytes height)
    for value in [width >> 8, width & 0xFF, height >> 8, height & 0xFF]:
        send_byte(value)

    # Send pixel data
    for pixel in pixels:
        send_byte(pixel)

try:
    img = Image.open(IMAGE_PATH).convert('L')  # Convert to grayscale
    img = img.resize((64, 64))  # Resize to small dimensions
    print(f"Transmitting image of size: {img.size}")
    send_sync_preamble()
    send_image(img)
finally:
    GPIO.cleanup()
