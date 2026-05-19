import serial
import threading

PORT = '/dev/ttyUSB0'  # Change if using a different port
BAUD = 9600

ser = serial.Serial(PORT, BAUD)

# 🧵 Thread to listen for incoming messages
def receive():
    while True:
        if ser.in_waiting > 0:
            msg = ser.readline().decode('utf-8', errors='ignore').strip()
            if msg:
                print(f"\n< Received: {msg}")
                print("You: ", end='', flush=True)

# 🧑‍💻 Main loop to send messages
def send():
    while True:
        try:
            msg = input("You: ")
            ser.write((msg + '\n').encode('utf-8'))
        except KeyboardInterrupt:
            print("\n[Exiting chat]")
            ser.close()
            break

# 🚀 Start the chat
print(f"[ Chat started on {PORT} at {BAUD} baud ]")
recv_thread = threading.Thread(target=receive, daemon=True)
recv_thread.start()
send()
