import RPi.GPIO as GPIO
from pypn5180.read5180 import read_full_tag_content
from pypn5180.iso_iec_15693 import iso_iec_15693
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT, initial=GPIO.HIGH)

start = time.time()
try:
    while True:
        reader = iso_iec_15693()
        text = read_full_tag_content(reader)
        reader.pn5180.spi.close()
        print(f"{time.time() - start:6.1f}s  {'OK  ' + text if text else 'FAIL'}", flush=True)
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()