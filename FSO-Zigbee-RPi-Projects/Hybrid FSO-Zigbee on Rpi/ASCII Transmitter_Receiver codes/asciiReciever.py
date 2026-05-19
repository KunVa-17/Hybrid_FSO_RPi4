import RPi.GPIO as GPIO
import time
import serial
import threading

# --- Configuration ---
PORT = '/dev/ttyUSB0'
BAUD = 9600
BIT_DURATION = 0.01
FSO_CHECK_INTERVAL = 2  # seconds

# --- Initialization ---
ser = serial.Serial(PORT, BAUD)
GPIO.setmode(GPIO.BCM)
PHOTO_PIN = 18
GPIO.setup(PHOTO_PIN, GPIO.IN)
USE_FSO = True

# --- Zigbee Fallback Receiver ---
def zigbee_receive():
    global USE_FSO
    while not USE_FSO:
        if ser.in_waiting:
            msg = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"< Zigbee Received: {msg}")

# --- FSO Bit Receiving ---
def read_bit():
    return '0' if GPIO.input(PHOTO_PIN) == GPIO.LOW else '1'

def wait_for_start(timeout=None):
    start = time.time()
    while True:
        if timeout and time.time() - start > timeout:
            return False
        if read_bit() == '1':
            time.sleep(BIT_DURATION)
            if read_bit() == '1':
                return True
        time.sleep(BIT_DURATION / 2)

def receive_byte():
    if not wait_for_start():
        return None
    bits = ''
    for _ in range(8):
        time.sleep(BIT_DURATION)
        bits += read_bit()
    time.sleep(BIT_DURATION)  # stop1
    stop1 = read_bit()
    time.sleep(BIT_DURATION)  # stop2
    stop2 = read_bit()

    if stop1 == '0' and stop2 == '0':
        return chr(int(bits, 2))
    else:
        return None

# --- FSO Link Monitor ---
def monitor_fso():
    global USE_FSO
    while not USE_FSO:
        time.sleep(FSO_CHECK_INTERVAL)
        if wait_for_start(timeout=BIT_DURATION * 4):
            USE_FSO = True
            print("\n[🔄 FSO restored]")
            ser.write(b"FSO_RESTORE\n")
            break

# --- Main Loop ---
def recv_loop():
    global USE_FSO
    print("[Starting Receiver]")
    while True:
        if USE_FSO:
            ch = receive_byte()
            if ch:
                print(ch, end='', flush=True)
            else:
                USE_FSO = False
                print("\n[⚠️ FSO framing error - fallback to Zigbee]")
                ser.write(b"FSO_FALLBACK\n")
                threading.Thread(target=zigbee_receive, daemon=True).start()
                threading.Thread(target=monitor_fso, daemon=True).start()
        else:
            time.sleep(0.1)

if __name__ == '__main__':
    try:
        recv_loop()
    except KeyboardInterrupt:
        GPIO.cleanup()
        ser.close()
