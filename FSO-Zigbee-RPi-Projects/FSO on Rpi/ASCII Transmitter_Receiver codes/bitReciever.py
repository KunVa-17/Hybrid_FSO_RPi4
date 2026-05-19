import RPi.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
PHOTO_PIN = 18
GPIO.setup(PHOTO_PIN, GPIO.IN)

def receive_data(bit_count, duration=0.1):
    received_bits = ''
    for _ in range(bit_count):
        bit = '0' if GPIO.input(PHOTO_PIN) == GPIO.LOW else '1'
        received_bits += bit
        time.sleep(duration)
    return received_bits

try:
    bits_to_receive = 8  # Number of bits expected
    data = receive_data(bits_to_receive)
    print(f"Received data: {data}")
finally:
    GPIO.cleanup()
