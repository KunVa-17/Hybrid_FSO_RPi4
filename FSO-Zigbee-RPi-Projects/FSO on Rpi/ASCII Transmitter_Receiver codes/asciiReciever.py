import RPi.GPIO as GPIO
import time

# GPIO Setup
GPIO.setmode(GPIO.BCM)
PHOTO_PIN = 18
GPIO.setup(PHOTO_PIN, GPIO.IN)

BIT_DURATION = 0.01  # seconds

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

    # Stop bits
    time.sleep(BIT_DURATION)
    stop1 = read_bit()
    time.sleep(BIT_DURATION)
    stop2 = read_bit()

    if stop1 == '0' and stop2 == '0':
        return chr(int(bits, 2))
    else:
        print("Framing error")
        time.sleep(0.1)
        return ''

try:
    print("Receiving ASCII text...")
    while True:
        char = receive_byte()
        if char:
            print(char, end='', flush=True)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
