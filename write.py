from pypn5180.write5180 import write_string_to_tag
import RPi.GPIO as GPIO
import time, os
text = input('Enter tag data:')

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)
GPIO.output(11, GPIO.HIGH)
time.sleep(0.01)

print("Hold tag to module")
if write_string_to_tag(text):
   print("Done...")
else:
   print("Error writing tag")
