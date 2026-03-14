import os, re
import signal
import subprocess
import sys
import threading

from RPi import GPIO
from queue import Queue

DEBUG = True

# SETTINGS
# ========

# The two pins that the encoder uses (BCM numbering).
GPIO_A = 33
GPIO_B = 31

# The pin that the knob's button is hooked up to. If you have no button, set
# this to None.
GPIO_BUTTON = None

VOLUME_MIN = 65    
VOLUME_MAX = 118

VOLUME_INCREMENT = 1
QUEUE = Queue()
EVENT = threading.Event()

def debug(str):
  if not DEBUG:
    return
  print(str)

class RotaryEncoder:
  def __init__(self, gpioA, gpioB, callback=None, buttonPin=None, buttonCallback=None):
    
    self.lastGpio = None
    self.gpioA    = gpioA
    self.gpioB    = gpioB
    self.callback = callback
    
    self.gpioButton     = buttonPin
    self.buttonCallback = buttonCallback
    
    self.levA = 0
    self.levB = 0
    
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(self.gpioA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(self.gpioB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    GPIO.add_event_detect(self.gpioA, GPIO.BOTH, self._callback)
    GPIO.add_event_detect(self.gpioB, GPIO.BOTH, self._callback)
    
    if self.gpioButton:
      GPIO.setup(self.gpioButton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      GPIO.add_event_detect(self.gpioButton, GPIO.FALLING, self._buttonCallback, bouncetime=500)
    
    
  def destroy(self):
    GPIO.remove_event_detect(self.gpioA)
    GPIO.remove_event_detect(self.gpioB)
    GPIO.cleanup()
    
  def _buttonCallback(self, channel):
    self.buttonCallback(GPIO.input(channel))
    
  def _callback(self, channel):
    level = GPIO.input(channel)
    if channel == self.gpioA:
      self.levA = level
    else:
      self.levB = level
      
    # Debounce.
    if channel == self.lastGpio:
      return
    
    # When both inputs are at 1, we'll fire a callback. If A was the most
    # recent pin set high, it'll be forward, and if B was the most recent pin
    # set high, it'll be reverse.
    self.lastGpio = channel
    if channel == self.gpioA and level == 1:
      if self.levB == 1:
        self.callback(1)
    elif channel == self.gpioB and level == 1:
      if self.levA == 1:
        self.callback(-1)


if __name__ == "__main__":
  
  gpioA = GPIO_A
  gpioB = GPIO_B
  gpioButton = GPIO_BUTTON
  
  def on_turn(delta):
    QUEUE.put(delta)
    EVENT.set()
    
  def consume_queue():
    while not QUEUE.empty():
      delta = QUEUE.get()
      handle_delta(delta)

  def get_current_volume():
    result = subprocess.run(['amixer', 'get', 'Speaker'], 
                          capture_output=True, text=True)
    match = re.search(r'Front Left: Playback (\d+)', result.stdout)
    print("volume: ", match.group(1), flush=True)
    return int(match.group(1)) if match else VOLUME_MIN
  
  def handle_delta(delta):
    if delta == 1:
      if get_current_volume() <= VOLUME_MIN:
        return
      subprocess.run(['amixer', 'set', 'Speaker', '1-'])
    else: 
      if get_current_volume() >= VOLUME_MAX:
        return
      print("up")
      subprocess.run(['amixer', 'set', 'Speaker', '1+'])
    
  def on_exit(a, b):
    print("Exiting...")
    encoder.destroy()
    sys.exit(0)
    
  debug("Volume knob using pins {} and {}".format(gpioA, gpioB))
  
  if gpioButton != None:
    debug("Volume button using pin {}".format(gpioButton))
  

  encoder = RotaryEncoder(GPIO_A, GPIO_B, callback=on_turn, buttonPin=GPIO_BUTTON)
  signal.signal(signal.SIGINT, on_exit)
  
  while True:
    EVENT.wait(1200)
    consume_queue()
    EVENT.clear()