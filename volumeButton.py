import re
import signal
import subprocess
import sys
import threading
from queue import Queue

from RPi import GPIO

# SETTINGS
# ========

# The two pins that the encoder uses (BOARD numbering).
GPIO_A = 33
GPIO_B = 31
GPIO_BUTTON = None
GPIO_HEADPHONE = 37

VOLUME_MIN = 100
VOLUME_MAX = 255
VOLUME_INCREMENT = 2

DEFAULT_HEADPHONE_VOLUME = 90
DEFAULT_SPEAKER_VOLUME = 112

# How long the jack signal must stay stable before we trust it.
# Slow/loose plug-ins can bounce for a while, so this is intentionally
# longer than a typical mechanical-switch debounce.
HEADPHONE_SETTLE_TIME = 0.4  # seconds

QUEUE = Queue()
EVENT = threading.Event()

_headphone_lock = threading.Lock()
_headphone_timer = None
headphones_plugged_in = False  # confirmed/debounced state


def _read_headphone_pin():
    return GPIO.input(GPIO_HEADPHONE) == 0


def _confirm_headphone_state():
    """Runs after HEADPHONE_SETTLE_TIME with no further jack events.
    Re-reads the pin; only commits if it still matches the reading that
    scheduled this timer (i.e. the state has actually settled)."""
    global headphones_plugged_in
    state = _read_headphone_pin()
    with _headphone_lock:
        if state != headphones_plugged_in:
            headphones_plugged_in = state
            print(f"headphones plugged in: {headphones_plugged_in}", flush=True)
            EVENT.set()


def on_headphone_jack_change(channel):
    global _headphone_timer
    with _headphone_lock:
        if _headphone_timer:
            _headphone_timer.cancel()
        _headphone_timer = threading.Timer(HEADPHONE_SETTLE_TIME, _confirm_headphone_state)
        _headphone_timer.daemon = True
        _headphone_timer.start()


def clean_up_headphone_jack_gpio():
    GPIO.remove_event_detect(GPIO_HEADPHONE)


class RotaryEncoder:
    def __init__(self, gpioA, gpioB, callback=None, buttonPin=None, buttonCallback=None):
        self.lastGpio = None
        self.gpioA = gpioA
        self.gpioB = gpioB
        self.callback = callback

        self.gpioButton = buttonPin
        self.buttonCallback = buttonCallback

        self.levA = 0
        self.levB = 0

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

        # When both inputs are at 1, fire a callback. If A was the most
        # recent pin set high, it's forward; if B was, it's reverse.
        self.lastGpio = channel
        if channel == self.gpioA and level == 1:
            if self.levB == 1:
                self.callback(1)
        elif channel == self.gpioB and level == 1:
            if self.levA == 1:
                self.callback(-1)


def get_current_volume():
    result = subprocess.run(['amixer', 'get', 'Playback'], capture_output=True, text=True)
    match = re.search(r'Front Left: (\d+)', result.stdout)
    volume = int(match.group(1)) if match else VOLUME_MIN
    print("volume: ", volume)
    return volume


def handle_delta(delta):
    current_volume = get_current_volume()
    if delta == 1:
        new_volume = max(VOLUME_MIN, current_volume - VOLUME_INCREMENT)
    else:
        new_volume = min(VOLUME_MAX, current_volume + VOLUME_INCREMENT)
    subprocess.run(['amixer', 'set', 'Playback', f'{new_volume}'])


def apply_output_routing():
    muted_output = "Speaker" if headphones_plugged_in else "Headphone"
    audio_output = "Headphone" if headphones_plugged_in else "Speaker"
    default_volume = DEFAULT_HEADPHONE_VOLUME if headphones_plugged_in else DEFAULT_SPEAKER_VOLUME
    subprocess.run(['amixer', 'set', muted_output, '0'])
    subprocess.run(['amixer', 'set', audio_output, f'{default_volume}'])


def consume_queue():
    apply_output_routing()
    while not QUEUE.empty():
        handle_delta(QUEUE.get())


def on_turn(delta):
    QUEUE.put(delta)
    EVENT.set()


if __name__ == "__main__":
    GPIO.setmode(GPIO.BOARD)

    subprocess.run(['amixer', 'set', 'Headphone', f'{DEFAULT_HEADPHONE_VOLUME}'])
    subprocess.run(['amixer', 'set', 'Speaker', f'{DEFAULT_SPEAKER_VOLUME}'])

    GPIO.setup(GPIO_HEADPHONE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    headphones_plugged_in = _read_headphone_pin()
    GPIO.add_event_detect(GPIO_HEADPHONE, GPIO.BOTH, on_headphone_jack_change)

    print("Volume knob using pins {} and {}".format(GPIO_A, GPIO_B))
    if GPIO_BUTTON is not None:
        print("Volume button using pin {}".format(GPIO_BUTTON))

    encoder = RotaryEncoder(GPIO_A, GPIO_B, callback=on_turn, buttonPin=GPIO_BUTTON)

    def on_exit(a, b):
        print("Exiting...")
        encoder.destroy()
        clean_up_headphone_jack_gpio()
        GPIO.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_exit)

    # Apply initial routing based on state at startup.
    apply_output_routing()

    while True:
        EVENT.wait(1200)
        consume_queue()
        EVENT.clear()