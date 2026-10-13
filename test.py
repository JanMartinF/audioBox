import RPi.GPIO as GPIO
import time
from pypn5180.read5180 import read_full_tag_content
from pypn5180.iso_iec_15693 import iso_iec_15693

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT, initial=GPIO.HIGH)  # never toggled

idleSleep = 1

try:
    iteration = 0
    while True:
        iteration += 1
        reader = iso_iec_15693()
        reader.pn5180.softwareReset()
        reader.pn5180.configureIsoIec15693Mode()

        text = read_full_tag_content(reader)
        reader.pn5180.rfOff()
        reader.pn5180.spi.close()
        print(f"[{iteration}] result={text}", flush=True)
        time.sleep(idleSleep)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Stopped.")
