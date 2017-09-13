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
import soapyDevice
import optparse
import datetime
import imageProcessing
import utils
import logging
from sdr import SDR
from waveFile import WaveFile

def getVersion():
    return "1.0b4"

def iqSaveProcess(dataFile, dataPipe):
  try:
    savedCount = 0
    while True:
      timeout = 10
      if dataPipe.poll(timeout):
        data = dataPipe.recv()
        if len(data) == 0:
          break
        
        data_ = data.astype('int32')
        
        print("Save:", len(data_), type(data_), type(data_[0]))
        
        fileName = "{}-{:05d}.iq".format(imageFileName, savedCount)
        data_.tofile(fileName)

        savedCount += 1
  
  except Exception as e:
      exc_type, exc_obj, tb = sys.exc_info()
      print("iqSaveProcess error:", e.args[0], tb.tb_lineno)
  except KeyboardInterrupt:
    pass
  except:
    pass

  print("")
  print("iqSaveProcess done")


def waterfallSaveProcess(imageWidth, sampleRate, frequencyKHz, outputFolder, imageFileName, dataPipe):
  try:
    savedCount = 0
    while True:
      timeout = 10
      if dataPipe.poll(timeout):
        data = dataPipe.recv()
        if len(data) == 0:
            break
        
        now = datetime.datetime.now()

        img = imageProcessing.createImageHeader(imageWidth, sampleRate, frequencyKHz)
        imgData = imageProcessing.imageToArray(img)

        imgDataOut = np.append(imgData, data, axis=0)
        imgOut = imageProcessing.imageFromArray(imgDataOut)

        fileName = "{}-{:05d}.jpg".format(imageFileName, savedCount)
        filePath = utils.makeFilePath(outputFolder, fileName)
        imgOut.save(filePath)
        
        savedCount += 1

        print("{:02d}:{:02d}:{:02d}: {} saved".format(now.hour, now.minute, now.second, fileName))

  except Exception as e:
      exc_type, exc_obj, tb = sys.exc_info()
      print("waterfallSaveProcess error:", e.args[0], tb.tb_lineno)
  except KeyboardInterrupt:
      pass
  except:
      pass

  print("")
  print("waterfallSaveProcess done")

def combineFiles(imageFileName, filesSavedCount):
  try:
    # Combine several images to a big one
    print("Combine files:")
    imgData = None
    for p in range(filesSavedCount):
        fileName = "{}-{:05d}.jpg".format(imageFileName, p)
        filePath = utils.makeFilePath(outputFolder, fileName)
        img = imageProcessing.loadImage(filePath)
        if imgData is None:
            # Add first image as is
            imgData = imageProcessing.imageToArray(img)
        else:
            # Remove header from other images
            width, height = img.size
            headerH = imageProcessing.getHeaderHeight()
            imgCrop = img.crop((0, headerH, width, height-headerH))
            data = imageProcessing.imageToArray(imgCrop)
            imgData = np.append(imgData, data, axis=0)
          
        print("{} added".format(fileName))
    
    # Save result
    fileName = "{}.jpg".format(imageFileName)
    filePath = utils.makeFilePath(outputFolder, fileName)
    imgOut = imageProcessing.imageFromArray(imgData)
    imgOut.save(filePath)
    print("Done, {} saved".format(filePath))

    # Remove originals
    for p in range(filesSavedCount):
        fileName = "{}-{:05d}.jpg".format(imageFileName, p)
        filePath = utils.makeFilePath(outputFolder, fileName)
        utils.deleteFile(filePath)

  except:
    print("combineFiles error: please add files manually")

def combineIQData(fileName, iqSavedCount):
    print("Combine files:")
    
    fileOutput = "{}.wav".format(fileName)
    
    for p in range(iqSavedCount):
        fileName = "{}-{:05d}.iq".format(fileName, p)
        fileData = open(fileName, "rb").read()
        
        if p == 0:
            # Create new file
            with open(fileOutput, "wb") as fileNew:
              wave = WaveFile(sample_rate=4000000)
              wave.saveHeader(fileNew)
              fileNew.write(fileData)
        else:
            # Append to the end
            with open(fileOutput, "ab") as fileAppend:
              fileAppend.write(fileData)

        utils.deleteFile(fileName)
          
    print("Done")


if __name__ == '__main__':
    print(utils.bold("SDR Waterfall2Img, version " + getVersion()))
    print(utils.bold("Usage: python3 sdr2pano.py  --f=frequencyInKHz [--sr=sampleRate] [--sdr=receiver] [--imagewidth=imageWidth] [--imagefile=fileName] [--average=N] [--saveIQ=1]"))
    print("")

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
        print("Warning: no receiver detected, simulation only")

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
    process = multiprocessing.Process(target=waterfallSaveProcess, args=params)
    process.start()
    
    # Start saving file process
    iqParentPipe, iqChildPipe = multiprocessing.Pipe()
    paramsIQ = [ imageFileName, iqParentPipe ]
    processIQ = multiprocessing.Process(target=iqSaveProcess, args=paramsIQ)
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

    #sys.exit(0)

    if filesSavedCount > 1:
        combineFiles(imageFileName, filesSavedCount)
    if iqSavedCount > 0:
        combineIQData(imageFileName, iqSavedCount)

