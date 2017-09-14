# Universal SDR waterfall image saver.
# (c) 2017 Dmitrii (dmitryelj@gmail.com)
#
# Installation:
# - install python3
# - install SoapySDR: https://github.com/pothosware/SoapySDR/wiki
# - install python libraries: pip3 install pillow numpy simplesoapy

import numpy as np
import os, sys, multiprocessing, time
import struct
#import soapyDevice
import optparse
import datetime
import imageProcessing
import fileProcessing
import utils
import logging
from sdr import SDR
from waveFile import WaveFile
if utils.isRaspberryPi():
  import libTFT

def getVersion():
    return "1.0b4"

def printIntro():
    print(utils.bold("SDR Waterfall2Img, version " + getVersion()))
    print(utils.bold("Usage: python3 wf2img.py  --f=frequencyInKHz [--sr=sampleRate] [--sdr=receiver] [--imagewidth=imageWidth] [--imagefile=fileName] [--average=N] [--saveIQ=1]"))
    print("Run 'nohup <python3 wf2img.py parameters> &' to run in the background")
    print("To combine files, saved before, use: python3 fileProcessing.py --file=fileName.jpg [--delete=true]")
    print("")

if __name__ == '__main__':
    printIntro()

    # Command line arguments
    parser = optparse.OptionParser()
    parser.add_option("--sdr", dest="sdr", help="receiver name", default="")
    parser.add_option("--sdrgain", dest="sdrgain", help="sdr gain settings", default="")
    parser.add_option("--sr", dest="samplerate", help="sample rate", default=2000000)
    parser.add_option("--f", dest="frequency", help="center frequency", default=101000000)
    parser.add_option("--imagewidth", dest="imagewidth", help="image width", default=1024)
    parser.add_option("--imagefile", dest="imagefile", help="output file name", default="")
    parser.add_option("--average", dest="average", help="stream average", default=64)
    parser.add_option("--markerS", dest="markerInS", help="time marker in seconds", default=60)
    parser.add_option("--saveIQ", dest="saveIQ", help="save IQ in HDSDR-compatible wav file", default=False)
    options, args = parser.parse_args()
    
    frequencyKHz = int(options.frequency)
    sampleRate = int(options.samplerate)
    imageFileName = options.imagefile
    imageWidth = int(options.imagewidth)
    average = int(options.average)
    markerInS = int(options.markerInS)
    markerRGB = [220,0,0]
    imageHeightLimit = 16384    # Not used yet
    saveIQ = isinstance(options.saveIQ, str) and (options.saveIQ == 'true' or options.saveIQ == '1' or options.saveIQ == 'True')
    outputFolder = utils.getAppFolder()
    
    sdr = SDR()
    # List all connected SoapySDR devices
    devices = sdr.listDevices()
    print("Receivers found:")
    for d in devices:
        print(d)
    print("")
    #print(devices[0])
    #print(type(devices[0]))    

    device = options.sdr if len(options.sdr) > 0 else sdr.findSoapyDevice(devices)
    print("Receiver selected:", device)
    if device is None and len(options.sdr) > 0:
        print("Error: receiver not found")
        sys.exit(1)
    if device is None:
        print("Error: no receiver detected")
        sys.exit(1) # Disable for debug only

    # Initialize SDR device
    sdr.initDevice(device)
    sdr.setSampleRate(sampleRate)
    sdr.setCenterFrequency(frequencyKHz)
    if len(options.sdrgain) > 0:
      sdr.setGainFromString(options.sdrgain)
    else:
      if device == 'sdrplay':
          sdr.setGainFromString("IFGR:40;RFGR:4")
      if device == 'rtlsdr':
          sdr.setGainFromString("TUNER:30")

    sdr.startStream()

    # Show status
    print("Receiver:", device)
    print("Sample rate:", sampleRate)
    print("Sample rates:", sdr.getSampleRates())
    print("Frequency (KHz):", frequencyKHz)
    print("Average, blocks:", average)
    print("Vertical markers (s):", markerInS)
    print("Gains:", sdr.getGains())
    print("Output folder:", outputFolder)
    print("Save IQ:", saveIQ)
    print("")

    print("Recording will be started after 4 seconds...")
    print("")
    time.sleep(4)

    print("Recording started, press Ctrl+C to stop")

    # Image file name - automatic/custom, without extention
    if len(imageFileName) == 0:
        dtStr = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        imageFileName = "{}-{}".format(dtStr, frequencyKHz)
    else:
        imageFileName = utils.getFileName(imageFileName)

    # Image data
    imgBlockSize = 64
    imgBlockNumber = 0
    imgBlockCombine = 2
    samplesToAdd = []
    filesSavedCount = 0
    iqSavedCount = 0
    
    # Start saving waterfall process
    parentPipe, childPipe = multiprocessing.Pipe()
    params = [ imageWidth, sampleRate, frequencyKHz, outputFolder, imageFileName, parentPipe ]
    process = multiprocessing.Process(target=fileProcessing.waterfallSaveProcess, args=params)
    process.start()
    
    # Start saving file process
    iqParentPipe, iqChildPipe = multiprocessing.Pipe()
    paramsIQ = [ imageFileName, iqParentPipe ]
    processIQ = multiprocessing.Process(target=fileProcessing.iqSaveProcess, args=paramsIQ)
    processIQ.start()

    now = datetime.datetime.now()
    timeInS = 24*60*now.hour + 60*now.minute + now.second
    diffInS = timeInS - markerInS*int(timeInS/markerInS)
    timeMarker = now - datetime.timedelta(seconds=diffInS)

    try:
        while True:
          fftData = np.zeros(imageWidth)
          for p in range(average):
              data = sdr.readStream()
              if len(data) > 0:
                # Save IQ (optional)
                if saveIQ:
                    iqChildPipe.send(data)
                    iqSavedCount += 1
                # Save FFT
                fft = imageProcessing.applyFFT(data, imageWidth)
                fftData += fft
          fftData /= average
          
          now = datetime.datetime.now()

          imgLine = imageProcessing.generateNewLine(imageWidth, fftData)
          # Add time marker
          diffInS = (now - timeMarker).total_seconds()
          if diffInS > markerInS:
              for x in range(10):
                imgLine[x] = markerRGB
              timeMarker = now
          samplesToAdd.append(imgLine)
          # Save, if ready
          if len(samplesToAdd) == imgBlockSize:
              childPipe.send(samplesToAdd)
              
              samplesToAdd = []
              filesSavedCount += 1

    except KeyboardInterrupt:
        pass
    except Exception as e:
        exc_type, exc_obj, tb = sys.exc_info()
        print("Error:", e.args[0], tb.tb_lineno)
    except:
        pass

    # Stop receiving
    sdr.stopStream()

    childPipe.send([])
    process.join(timeout=10)

    iqChildPipe.send([])
    processIQ.join(timeout=10)

    childPipe.close()
    parentPipe.close()
    iqChildPipe.close()
    iqParentPipe.close()

    print("")

    # Combine files
    print("Files saved: {}".format(filesSavedCount))

    if filesSavedCount > 1:
        fileProcessing.combineImages(imageFileName, filesSavedCount)
    if iqSavedCount > 0:
        fileProcessing.combineIQData(imageFileName, iqSavedCount)

