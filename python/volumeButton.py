import os, re
import signal
import subprocess
import sys
import threading

from RPi import GPIO
from queue import Queue

# SETTINGS
# ========

# The two pins that the encoder uses (BCM numbering).
GPIO_A = 33
GPIO_B = 31
GPIO_BUTTON = None

VOLUME_MIN = 100
VOLUME_MAX = 255

DEFAULT_HEADPHONE_VOLUME = 90
DEFAULT_SPEAKER_VOLUME = 112
subprocess.run(['amixer', 'set', 'Headphone', f'{DEFAULT_HEADPHONE_VOLUME}'])
subprocess.run(['amixer', 'set', 'Speaker', f'{DEFAULT_SPEAKER_VOLUME}'])

VOLUME_INCREMENT = 1 
QUEUE = Queue()
EVENT = threading.Event()


#TODOJAN FIX THIS
def on_headphone_jack_change(event):
  print("headphone event: ", event, flush=True)
  EVENT.set()

def clean_up_headphone_jack_gpio():
  GPIO.remove_event_detect(GPIO_HEADPHONE)
  GPIO.cleanup()

GPIO_HEADPHONE = 37
GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_HEADPHONE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_HEADPHONE, GPIO.BOTH, on_headphone_jack_change)


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
    headphones_plugged_in = GPIO.input(GPIO_HEADPHONE) == 0
    muted_output = "Speaker" if headphones_plugged_in else "Headphone"
    audio_output = "Headphone" if headphones_plugged_in else "Speaker"
    subprocess.run(['amixer', 'set', f'{muted_output}', f'0'])
    subprocess.run(['amixer', 'set', f'{audio_output}', f'{DEFAULT_HEADPHONE_VOLUME if headphones_plugged_in else DEFAULT_SPEAKER_VOLUME}']) 
    while not QUEUE.empty():
      delta = QUEUE.get()
      handle_delta(delta)

  def get_current_volume():
    result = subprocess.run(['amixer', 'get', f'Playback'], 
                          capture_output=True, text=True)
    match = re.search(r'Front Left: (\d+)', result.stdout)
    print("volume: ", match.group(1))
    return int(match.group(1)) if match else VOLUME_MIN
  
  def handle_delta(delta):
    current_volume = get_current_volume()
    if delta == 1:
      if current_volume <= VOLUME_MIN:
        subprocess.run(['amixer', 'set', 'Playback', f'{VOLUME_MIN}'])
        return
      subprocess.run(['amixer', 'set', f'Playback', f'{current_volume - VOLUME_INCREMENT}'])
    else: 
      if current_volume >= VOLUME_MAX:
        subprocess.run(['amixer', 'set', f'Playback', f'{VOLUME_MAX}'])
        return
      subprocess.run(['amixer', 'set', f'Playback', f'{current_volume + VOLUME_INCREMENT}'])

  def on_exit(a, b):
    print("Exiting...")
    encoder.destroy()
    clean_up_headphone_jack_gpio()
    sys.exit(0)
    
  print("Volume knob using pins {} and {}".format(gpioA, gpioB))
  
  if gpioButton != None:
    print("Volume button using pin {}".format(gpioButton))
  

  encoder = RotaryEncoder(GPIO_A, GPIO_B, callback=on_turn, buttonPin=GPIO_BUTTON)
  signal.signal(signal.SIGINT, on_exit)
  
  while True:
    EVENT.wait(1200)
    consume_queue()
    EVENT.clear()