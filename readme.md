SDR-Waterfall2Img - universal SDR Waterfall Image Saver.

# Usage
Application is intended to process and save data from different SDR receiver and save it in the waterfall format.

Features:
- Unlimited (almost) waterfall size and lots of parameters to tune
- Support of different SDR receivers by using vendor neutral SoapySDR API
- Cross platform, works anywhere, from Windows and OSX to Raspberry Pi

# Screenshots
![FM band](/screenshots/aviaBand.jpg)
![Avia band](/screenshots/fmBand.jpg)

# Command line examples

**Get receiver info (name, available gains, etc)**

python3 info.py

**Use SDRplay**

python3 wf2img.py --sdr=sdrplay --f=101000000 --sr=8000000 --sdrgain="IFGR:30;RFGR:2" --average=64

**Use RTLSDR**

python3 wf2img.py --sdr=rtlsdr --imagewidth=1024 --sr=2048000 --f=122000000 --average=32 --sdrgain="TUNER:40"

(Important: image width should be power of 2: 512, 1024, 2048, etc)

On some computers additional parameters may be required:

python3 wf2img.py --sdr="driver=rtlsdr,rtl=1" --imagewidth=1024 --sr=2048000 --f=122000000 --average=32 --sdrgain="TUNER:40"

**Use HackRF**

python3 wf2img.py --sdr=hackrf --imagewidth=4096 --sr=20000000 --f=127000000 --average=64 --sdrgain="AMP:0;LNA:37;VGA:24"

**Recording in the specified time**

python3 wf2img.py --sdr=rtlsdr --average=4 --f=101000000 --tStart="18:40" --tEnd="19:00"
or
python3 wf2img.py --sdr=rtlsdr --average=4 --f=101000000 --tStart="18:40" --tLimit=1200

**Batch processing (several recordings in different times)**

python3 wf2img.py --sdr=rtlsdr --average=4 --batch="122000000;16:18;16:19;126000000;16:20;16:21"

**Save IQ (WAV)**

python3 wf2img.py --sdr=sdrplay --f=101000000 --sr=8000000 --sdrgain="IFGR:30;RFGR:2" --saveIQ=1 --saveWaterfall=0

**Save IQ + Waterfall (not recommended on weak computers like Raspberry Pi)**

python3 wf2img.py --sdr=sdrplay --f=101000000 --sr=8000000 --sdrgain="IFGR:30;RFGR:2" --saveIQ=1 --saveWaterfall=1

**Convert IQ WAV to Waterfall image**

python wav2img.py --average=4 --imagewidth=2048 --input=HDSDR_20171018_222123Z_122000kHz_RF.wav

(Important: image width should be power of 2: 512, 1024, 2048, etc)

# Installation and requirements

### Windows install:

- Install Python 3 from https://www.python.org/downloads/ (I used C:\Python3 folder)

- Run C:\Python3\Scripts\pip.exe install pillow numpy

- Install SoapySDR binaries. Easiest way - to install Pothos Core, it contains all binaries:
https://github.com/pothosware/PothosCore/wiki/Downloads

- Download and unpack SDR-Waterfall2Img from this page

- Run and enjoy

### Raspberry Pi:

sudo apt-get update

Install Python 3.6 (a pity, but simplesoapy requires this):

sudo apt-get install build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev
wget https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tar.xz
tar xf Python-3.6.0.tar.xz
cd Python-3.6.0
./configure
make -j4
sudo make altinstall

Install SoapySDR
sudo apt-get install python-dev swig
git clone https://github.com/pothosware/SoapySDR.git

Follow the instructions:
https://github.com/pothosware/SoapySDR/wiki/BuildGuide

sudo pip-3.6 install pillow numpy
git clone https://github.com/dmitryelj/SDR-Waterfall2Img.git

### OSX:

Build SoapySDR:
git clone https://github.com/pothosware/SoapySDR.git

Follow the instructions:
https://github.com/pothosware/SoapySDR/wiki/BuildGuide

sudo pip-3.2 install pillow numpy
git clone https://github.com/dmitryelj/SDR-Waterfall2Img.git

Optional: If the app is not working with "soapysdr not found" error, copy SoapySDR python libraries from 'osx' or "SoapySDR/build" subfolder to the folder script
