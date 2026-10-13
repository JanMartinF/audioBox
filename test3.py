import RPi.GPIO as GPIO, time
from pypn5180.iso_iec_15693 import iso_iec_15693
from pypn5180.read5180 import read_full_tag_content
# GPIO.cleanup()
# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)
# GPIO.setup(11, GPIO.OUT, initial=GPIO.HIGH)
counter = 0
reader = iso_iec_15693()
success_counter = 0
while True:
   counter += 1
   print("counter: ", counter, '\nsuccesse: ', success_counter)
   time.sleep(1)
   GPIO.output(11, GPIO.HIGH)

   # time.sleep(1)
   # reader.pn5180.rfOn(0x00)
   # reader.pn5180.softwareReset()
   reader.pn5180.configureIsoIec15693Mode()
   time.sleep(1)

   reader.pn5180.selfTest()
   text = read_full_tag_content(reader)
   if text:
      print("IT WORKS: ", text, "\n\n\n\n\n\n")
      success_counter += 1
   # reader.pn5180.spi.close()
   reader.pn5180.rfOff()
   GPIO.output(11, GPIO.LOW)
GPIO.cleanup()