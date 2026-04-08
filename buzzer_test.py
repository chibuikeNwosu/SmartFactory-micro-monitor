import RPi.GPIO as GPIO
import time

BUZZER = 18  # I/O pin

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER, GPIO.OUT)

try:
    while True:
        print("Buzzer ON")
        GPIO.output(BUZZER, 0)
        time.sleep(10)

        print("Buzzer OFF")
        GPIO.output(BUZZER, 1)
        time.sleep(10)

except KeyboardInterrupt:
    GPIO.cleanup()
