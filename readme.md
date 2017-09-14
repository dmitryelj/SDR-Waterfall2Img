SDR-Waterfall2Img - universal SDR Waterfall Image Saver.

# Usage
Application is intended to process and save data from different SDR receiver and save it in the waterfall format.

Features:
- Unlimited (almost) waterfall size and lots of parameters to tune
- Support of different SDR receivers by using Python and vendor neutral SoapySDR API
- Cross platform, from Windows and OSX to Raspberry Pi

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

If recording is not starting, additional parameters can be added:

python3 wf2img.py --sdr="driver=rtlsdr,rtl=1" --imagewidth=1024 --sr=2048000 --f=122000000 --average=32 --sdrgain="TUNER:40"

**Use HackRF**

python3 wf2img.py --sdr=hackrf --imagewidth=4096 --sr=20000000 --f=127000000 --average=64 --sdrgain="AMP:0;LNA:37;VGA:24" 

# Installation and requirements

### Windows install:

- Install Python 3 from https://www.python.org/downloads/ (I used C:\Python3 folder)

- Run C:\Python3\Scripts\pip.exe install pillow numpy simplesoapy

- Install SoapySDR binaries. Easiest way - to install Pothos Core, it contains all binaries:
https://github.com/pothosware/PothosCore/wiki/Downloads

- Download and unpack SDR-Waterfall2Img from this page

- Run and enjoy

### Raspberry Pi:

sudo apt-get update

Install SoapySDR

sudo apt-get install python-dev swig  
git clone https://github.com/pothosware/SoapySDR.git  
mkdir build  
cd build  
cmake ..  
make -j4  
sudo make install  
sudo ldconfig #needed on debian systems  

sudo pip3 install pillow numpy  
git clone https://github.com/dmitryelj/SDR-Waterfall2Img.git  

In the case of getting "SoapySDR not found" error, copy files "SoapySDR.py" and "_SoapySDR.so" from SoapySDR/build/python3 to SDR-Waterfall2Img folder  

### OSX:

Build SoapySDR:  
git clone https://github.com/pothosware/SoapySDR.git  

Follow the instructions:  
https://github.com/pothosware/SoapySDR/wiki/BuildGuide  

sudo pip-3.2 install pillow numpy simplesoapy  
git clone https://github.com/dmitryelj/SDR-Waterfall2Img.git  

Optional: If the app is not working with "soapysdr not found" error, copy SoapySDR python libraries from 'osx' or "SoapySDR/build" subfolder to the folder script  
