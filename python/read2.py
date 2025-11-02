import RPi.GPIO as GPIO
from pypn5180.read5180 import read_full_tag_content
from pypn5180.iso_iec_15693 import iso_iec_15693
import vlc
import time, os

allAudios = os.listdir("./audio")

idleSleep = 1
resetSleep = 0.01
currentAudio = None
placementCounter = 0
counterLimit = 4
# VLC_INSTANCE = vlc.Instance('--aout=alsa')
# vlc.Instance('--aout=alsa')s
media_player = vlc.MediaPlayer()

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)

GPIO.output(11, GPIO.HIGH)
# time.sleep(resetSleep)
# time.sleep(resetSleep)
# GPIO.output(11, GPIO.LOW)
reader = iso_iec_15693()
try:
	while True:
		try:
			reader.pn5180.rfOn(reader.pn5180.RF_ON_MODE["STANDARD"])
			time.sleep(0.01)  # Brief delay for RF to stabilize
			text = read_full_tag_content(reader)
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
				
			# GPIO.output(11, GPIO.LOW)
			reader.pn5180.rfOff()
			time.sleep(idleSleep - resetSleep)
		except Exception as e:
			# GPIO.output(11, GPIO.LOW)
			reader.pn5180.rfOff()
			time.sleep(idleSleep - resetSleep)
except KeyboardInterrupt:
	print("Closing program", flush=True)
