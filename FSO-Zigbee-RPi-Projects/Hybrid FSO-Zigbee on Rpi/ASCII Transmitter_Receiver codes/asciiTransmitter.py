import RPi.GPIO as GPIO
import time
import serial
import threading

# --- Configuration ---
PORT = '/dev/ttyUSB0'
BAUD = 9600
BIT_DURATION = 0.01

# --- Initialization ---
ser = serial.Serial(PORT, BAUD)
GPIO.setmode(GPIO.BCM)
LASER_PIN = 23
GPIO.setup(LASER_PIN, GPIO.OUT)
USE_FSO = True

# --- Zigbee Signaling Receiver ---
def zigbee_monitor():
    global USE_FSO
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line == 'FSO_FALLBACK':
                USE_FSO = False
                print("[Transmitter: switching to Zigbee fallback]")
            elif line == 'FSO_RESTORE':
                USE_FSO = True
                print("[Transmitter: resuming FSO]")

# --- FSO Bit/Binary Transmission ---
def send_bit(bit):
    GPIO.output(LASER_PIN, GPIO.LOW if bit == '1' else GPIO.HIGH)
    time.sleep(BIT_DURATION)

def send_byte(ch):
    b = format(ord(ch), '08b')
    for bit in '11' + b + '00':
        send_bit(bit)

# --- Main Transmit Loop ---
def transmit():
    threading.Thread(target=zigbee_monitor, daemon=True).start()
    GPIO.output(LASER_PIN, GPIO.HIGH)
    print("[Transmitter started]")

    while True:
        msg = input("Enter message: ")
        if msg.lower() == 'exit':
            break

        mode = 'FSO' if USE_FSO else 'Zigbee'
        print(f"[Sending over {mode}]")

        for ch in msg + '\n':
            send_byte(ch)

        GPIO.output(LASER_PIN, GPIO.HIGH)  # Back to idle

        if not USE_FSO:
            ser.write((msg + '\n').encode())

if __name__ == '__main__':
    try:
        transmit()
    finally:
        GPIO.cleanup()
        ser.close()
