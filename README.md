# AudioBox
## Raspberry-pi 2W setup

### Install Raspberry Pi OS Lite
- using Raspberry PI imager is advised

### Basic Raspi setup
1. Enable SPI (needed for the PN5180 reader): sudo raspi-config -> Interface Options -> SPI -> Enable, then reboot.
2.  Install system deps: sudo apt update && sudo apt install -y python3-venv python3-pip vlc libvlc-dev
3. Create venv + packages: python3 -m venv /home/jan/env, then activate and pip install RPi.GPIO python-vlc
need spidev-3.2 at least installed on the raspberry


### Audio HAT setup (WM8960-Audio-HAT: https://www.waveshare.com/wiki/)
1. install git and clone https://github.com/waveshare/WM8960-Audio-HAT
2.  - cd WM8960-Audio-HAT
    - sudo chmod +x install.sh
    - sudo ./install.sh 
    - sudo reboot

### Setting up services for basic functionality
1. create/copy service files:
- sudo cp audio_box.service /etc/systemd/system/
- sudo cp audio_volume.service /etc/systemd/system/
2. load services
- sudo systemctl daemon-reload
- sudo systemctl enable audio_box audio_volume
- sudo systemctl start audio_box audio_volume


### Cable management

| NXP5180 |  Raspi Header  |
|---------|----------------|
|+5V      |   2 - 5V       |
|+3V3     |   1 - 3V3      |
|RST      |   17- 3V3      |
|NSS      |   24- SPI0-CS0 |
|MOSI     |   19- SPI0-MOSI|
|MISO     |   21- SPI0-MISO|
|SCK      |   23- SPI0-SCLK|
|BUSY     |    -         |
|GND      |   6 - GND    |
|GPIO     |    -         |
|IRQ      |    -         |
|AUX      |    -         |
|REQ      |    -         |
