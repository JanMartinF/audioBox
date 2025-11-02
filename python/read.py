import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import vlc
import time, os

allAudios = os.listdir("./audio")

reader = SimpleMFRC522()
idleSleep = 1
playbackSleep = 0.5
currentAudio = ''
placementCounter = 0
counterLimit = 5
global VLC_INSTANCE
VLC_INSTANCE = None
try:
	print("starting ...")
	while True:
		try:
			id, text = reader.read_no_block()
			print("text?! ", text)
			print("id?! ", id)
			if not text and placementCounter <= counterLimit:
				placementCounter += 1
			elif text: 
				text = text.strip()
				placementCounter = 0
				if placementCounter > counterLimit and VLC_INSTANCE:
					VLC_INSTANCE.stop()
					currentAudio = ''
				print("tag content: ", text)
				if (text in allAudios or text.startswith('https')) and currentAudio != text:
					currentAudio = text
					if text.startswith('https'):
						VLC_INSTANCE = vlc.MediaPlayer(text)
					else:
						VLC_INSTANCE = vlc.MediaPlayer('audio/'+text)
					print("Playing audio ... ", text)
					VLC_INSTANCE.play()
			time.sleep(idleSleep)
		except Exception as e:
			print(f"Error reading tag: {e}")
			time.sleep(idleSleep)
except KeyboardInterrupt:
	print("Closing program")
finally:
	GPIO.cleanup()
