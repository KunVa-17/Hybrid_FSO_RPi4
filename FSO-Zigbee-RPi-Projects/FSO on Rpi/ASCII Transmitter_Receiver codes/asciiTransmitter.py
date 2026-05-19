import RPi.GPIO as GPIO
import time

# GPIO Setup
GPIO.setmode(GPIO.BCM)
LASER_PIN = 23
GPIO.setup(LASER_PIN, GPIO.OUT)

BIT_DURATION = 0.01  # seconds

def send_bit(bit):
    GPIO.output(LASER_PIN, GPIO.HIGH if bit == '0' else GPIO.LOW)
    time.sleep(BIT_DURATION)

def send_byte(char):
    binary = format(ord(char), '08b')  # Convert char to 8-bit binary
    # Frame: Start bits (1, 1), then data, then Stop bits (0, 0)
    send_bit('1')
    send_bit('1')
    for b in binary:
        send_bit(b)
    send_bit('0')
    send_bit('0')

def idle_loop():
    GPIO.output(LASER_PIN, GPIO.HIGH)  # Idle state: laser ON
    while True:
        msg = input("Enter text to send (or 'exit'): ")
        if msg.lower() == 'exit':
            break
        for char in msg:
            send_byte(char)
            time.sleep(0.05)  # Optional inter-character delay
        GPIO.output(LASER_PIN, GPIO.HIGH)  # Return to idle

try:
    idle_loop()
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
