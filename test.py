import RPi.GPIO as GPIO
from pypn5180.read5180 import read_full_tag_content
from pypn5180.iso_iec_15693 import iso_iec_15693
import time
import os

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)

def count_open_files():
    """Count number of open file descriptors for this process"""
    pid = os.getpid()
    return len(os.listdir(f'/proc/{pid}/fd'))

print("Starting file descriptor test...")
print(f"Initial open files: {count_open_files()}")

try:
    for i in range(20):  # Test 20 iterations
        GPIO.output(11, GPIO.HIGH)
        time.sleep(0.01)
        
        reader = iso_iec_15693()
        text = read_full_tag_content(reader)
        
        # TEST A: Without cleanup (comment out next line)
        reader.pn5180.spi.close()
        # TEST B: With cleanup (uncomment above line)
        
        GPIO.output(11, GPIO.LOW)
        time.sleep(0.1)
        
        if (i + 1) % 5 == 0:
            print(f"After {i+1} iterations: {count_open_files()} open files")
            
except KeyboardInterrupt:
    print("\nStopped")
finally:
    GPIO.output(11, GPIO.LOW)
    GPIO.cleanup()
    print(f"Final open files: {count_open_files()}")