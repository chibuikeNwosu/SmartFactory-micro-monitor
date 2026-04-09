import RPi.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

print("SmartFactory Buzzer Test")
print("Buzzer will beep 5 times...")
print("Press CTRL+C to stop\n")

try:
    for i in range(5):
        print(f"Beep {i+1}...")
        GPIO.output(17, GPIO.HIGH)  # Buzzer ON
        time.sleep(0.5)
        GPIO.output(17, GPIO.LOW)   # Buzzer OFF
        time.sleep(0.5)

    print("\nTest complete! Buzzer working! ?")

except KeyboardInterrupt:
    print("\nTest stopped. Goodbye!")

finally:
    GPIO.cleanup()
