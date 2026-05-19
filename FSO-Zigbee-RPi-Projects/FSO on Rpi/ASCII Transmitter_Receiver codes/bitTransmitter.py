import RPi.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
LASER_PIN = 23
GPIO.setup(LASER_PIN, GPIO.OUT)

def send_bit(bit, duration=0.1):
    GPIO.output(LASER_PIN, GPIO.HIGH if bit == '1' else GPIO.LOW)
    time.sleep(duration)

def send_data(data):
    for bit in data:
        send_bit(bit)
    GPIO.output(LASER_PIN, GPIO.LOW)  # Ensure laser is off after transmission

try:
    binary_data = input("Enter a binary number to transmit: ")
    # Validate input
    if all(c in '01' for c in binary_data):
        send_data(binary_data)
    else:
        print("Invalid input. Please enter a binary number consisting of 0s and 1s only.")
finally:
    GPIO.cleanup()
