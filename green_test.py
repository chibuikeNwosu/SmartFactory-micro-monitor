import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)

print("Testing GREEN LED on GPIO23...")
print("Green should light up now!")

GPIO.output(23, GPIO.HIGH)
time.sleep(5)
GPIO.output(23, GPIO.LOW)

print("Done!")
GPIO.cleanup()
