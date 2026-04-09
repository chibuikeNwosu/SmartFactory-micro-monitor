import RPi.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)  # Green
GPIO.setup(22, GPIO.OUT)  # Red
GPIO.setup(27, GPIO.OUT)  # Blue

def all_off():
    GPIO.output(23, GPIO.LOW)
    GPIO.output(22, GPIO.LOW)
    GPIO.output(27, GPIO.LOW)

print("SmartFactory RGB LED Test")
print("Testing each colour...\n")

try:
    # Test Red
    print("RED...")
    all_off()
    GPIO.output(22, GPIO.HIGH)
    time.sleep(2)

    # Test Green
    print("GREEN...")
    all_off()
    GPIO.output(23, GPIO.HIGH)
    time.sleep(2)

    # Test Blue
    print("BLUE...")
    all_off()
    GPIO.output(27, GPIO.HIGH)
    time.sleep(2)

    # Test Yellow (Red + Green)
    print("YELLOW...")
    all_off()
    GPIO.output(22, GPIO.HIGH)
    GPIO.output(23, GPIO.HIGH)
    time.sleep(2)

    # Test White (All on)
    print("WHITE...")
    all_off()
    GPIO.output(22, GPIO.HIGH)
    GPIO.output(23, GPIO.HIGH)
    GPIO.output(27, GPIO.HIGH)
    time.sleep(2)

    all_off()
    print("\nTest complete! RGB LED working! ?")

except KeyboardInterrupt:
    print("\nTest stopped. Goodbye!")

finally:
    GPIO.cleanup()
