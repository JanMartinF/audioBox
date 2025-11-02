import RPi.GPIO as GPIO
from pypn5180.read5180 import read_full_tag_content
from pypn5180.iso_iec_15693 import iso_iec_15693
import vlc
import time, os

def count_open_files():
    """Count number of open file descriptors for this process"""
    pid = os.getpid()
    return len(os.listdir(f'/proc/{pid}/fd'))

allAudios = os.listdir("./audio")

idleSleep = 1
resetSleep = 0.01
currentAudio = None
placementCounter = 0
counterLimit = 4
# VLC_INSTANCE = vlc.Instance('--aout=alsa')
media_player = vlc.MediaPlayer()

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)
print(f"Initial open files: {count_open_files()} for pid {os.getpid()}", flush=True)

try:
	while True:
		try:
			GPIO.setup(11, GPIO.OUT, initial=GPIO.HIGH)
			time.sleep(resetSleep)
			reader = iso_iec_15693()
			text = read_full_tag_content(reader)
			reader.pn5180.spi.close()
			if text: 
				placementCounter = 0
				print("tag content: ", text, flush=True)
				if text in allAudios and currentAudio != text:
					currentAudio = text
					if media_player.is_playing(): media_player.stop()
					media = vlc.Media('audio/' + text)
					media_player.set_media(media)
					media_player.play()

				if text.startswith('https') and currentAudio != text:
						currentAudio = text
						if media_player.is_playing(): media_player.stop()
						media = vlc.Media(text)
						media_player.set_media(media)
						media_player.play()
			else:
				if placementCounter >= counterLimit:
					currentAudio = None
					if media_player.is_playing(): media_player.stop()
				else:
					placementCounter += 1
				
			GPIO.output(11, GPIO.LOW)
			time.sleep(idleSleep - resetSleep)
		except Exception as e:
			GPIO.output(11, GPIO.LOW)
			time.sleep(idleSleep - resetSleep)
except KeyboardInterrupt:
	print("Closing program", flush=True)
	print(f"Final open files: {count_open_files()}")
