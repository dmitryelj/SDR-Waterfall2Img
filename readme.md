Universal SDR Waterfall Image Saver.
(c) 2017 Dmitrii (dmitryelj@gmail.com)

Usage:
Application is intended to process and save data from SDR receiver and save it in the waterfall format.

Features:
- Unlimited (almost) waterfall size and lots of parameters to tune
- Support of different SDR receivers by using Python and vendor neutral SoapySDR API
- Cross platform, from Windows and OSX to Raspberry Pi

Examples:
python3 wf2img.py --sdr=hackrf --f=101000000 --sr=8000000 --imagewidth=1024 --average=32

SDR custom settings:
1) SDRplay
python3 wf2img.py --sdr=sdrplay --f=101000000 --sr=8000000 --sdrgain="IFGR:30;RFGR:2"

2) RTLSDR
python3 wf2img.py --sdr=rtlsdr --imagewidth=1024 --sr=2048000 --f=122000000 --average=32 --sdrgain="TUNER:40"

If recording is not starting, additional parameters can be added:
python3 wf2img.py --sdr="driver=rtlsdr,rtl=1" --imagewidth=1024 --sr=2048000 --f=122000000 --average=32 --sdrgain="TUNER:40"

Installation and requirements

1) Python3
https://www.python.org/downloads/

2) SoapySDR
https://github.com/pothosware/SoapySDR/wiki#installation

Easiest way - install Pothos Core, it contains all binaries
https://github.com/pothosware/PothosCore/wiki/Downloads

3) Additional libraries
pip3 install pillow numpy simplesoapy

4) OSX only
copy libraries from 'osx' folder to the folder script

