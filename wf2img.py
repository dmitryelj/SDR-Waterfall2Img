# Universal SDR waterfall image saver.
# (c) 2017 Dmitrii (dmitryelj@gmail.com)
#
# Installation:
# - install python3
# - install SoapySDR: https://github.com/pothosware/SoapySDR/wiki
# - install python libraries: pip3 install pillow numpy simplesoapy

import numpy as np
import os, sys, time
import simplesoapy
import optparse
import datetime
import imageProcessing
import utils
import logging

class SDR(object):
    def __init__(self):
        self.isInit = False
        self.sdr = None
        self.name = ""

    def listDevices(self):
        devices = simplesoapy.detect_devices(as_string=False)
        return devices

    def initDevice(self, name = None, driverName = None):
        if name is None and driverName is None:
            self.name = "fake"
            return

        # Search by additional parameter, like 'driver=rtlsdr,rtl=1'
        if ',' in name:
            self.sdr = simplesoapy.SoapyDevice(name)
            self.name = driverName
            return

        # Search by driver
        if driverName is not None:
            self.sdr = simplesoapy.SoapyDevice('driver=' + driverName)
            self.name = driverName
            return

        # Search by driver or description
        devices = self.listDevices()
        for d in devices:
            driver = d['driver']
            description = d['label']
            if name == driver or name in description:
                self.sdr = simplesoapy.SoapyDevice('driver=' + driver)
                self.name = driver
                return
            
        self.name = "-"

    def findSoapyDevice(self, devices):
        deviceNames = map(lambda d: d['driver'], devices)
        for name in deviceNames:
            if name == 'sdrplay' or name == 'hackrf' or name == 'rtlsdr':
                return name
            
        return None

    def getSampleRates(self):
        if self.sdr is None:
            return [2000000.0]
        
        return self.sdr.list_sample_rates()

    def getGains(self):
        if self.sdr is None: return "-"

        s = ""
        gains = self.sdr.list_gains()
        for g in gains:
            s += "{}:{}; ".format(g, self.sdr.get_gain_range(amp_name=g))
        return s

    def setGainFromString(self, gainStr):
        if self.sdr is None: return
      
        # String like IFGR:30;RFGR:2
        items = gainStr.split(";")
        for i in items:
            values = i.split(":")
            name = values[0]
            value = values[1]
            print("Set gain:", name, "value:", value)
            self.sdr.set_gain(name, float(value))

    def setSampleRate(self, samplerate):
        if self.sdr is not None:
            self.sdr.sample_rate = samplerate

    def setCenterFrequency(self, frequency):
        if self.sdr is not None:
            self.sdr.freq = frequency

    def startStream(self):
        if self.sdr is not None:
          # Setup base buffer and start receiving samples. Base buffer size is determined
          # by SoapySDR.Device.getStreamMTU(). If getStreamMTU() is not implemented by driver,
          # SoapyDevice.default_buffer_size is used instead
          self.sdr.start_stream(buffer_size=16384)

    def stopStream(self):
        if self.sdr is not None:
            self.sdr.stop_stream()

    def readStream(self):
        if self.sdr is not None:
            res = self.sdr.read_stream()
            #print("Data received", res)
            return self.sdr.buffer if res.ret > 0 else []
        else:
            randData = np.random.rand(16384)
            time.sleep(0.01)
            return randData

def getVersion():
  return "1.0b3"

if __name__ == '__main__':
    print(utils.bold("SDR Waterfall2Img, version " + getVersion()))
    print(utils.bold("Usage: python3 sdr2pano.py  --f=frequencyInKHz [--sr=sampleRate] [--sdr=receiver] [--imagewidth=imageWidth] [--imagefile=fileName] [--average=N]"))
    print("")

    logger = logging.getLogger("simplesoapy")
    logger.propagate = False
    logger.setLevel(logging.ERROR)

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
    options, args = parser.parse_args()
    
    frequencyKHz = int(options.frequency)
    sampleRate = int(options.samplerate)
    imageFileName = options.imagefile
    imageWidth = int(options.imagewidth)
    average = int(options.average)
    markerInS = int(options.markerInS)
    markerRGB = [220,0,0]
    imageHeightLimit = 16384    # Not used yet
    saveIQ = False              # Not used yet
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
              img = imageProcessing.createImageHeader(imageWidth, sampleRate, frequencyKHz)
              imgData = imageProcessing.imageToArray(img)

              imgDataOut = np.append(imgData, samplesToAdd, axis=0)
              imgOut = imageProcessing.imageFromArray(imgDataOut)
              
              fileName = "{}-{:05d}.jpg".format(imageFileName, filesSavedCount)
              filePath = utils.makeFilePath(outputFolder, fileName)
              imgOut.save(filePath)

              print("{:02d}:{:02d}:{:02d}: {} saved".format(now.hour, now.minute, now.second, fileName))

              samplesToAdd = []
              filesSavedCount += 1

          # np.save("data.wav", samples)
          # samples.astype('int16').tofile("data.iq")

    except KeyboardInterrupt:
        pass
    except:
        pass

    # Stop receiving
    sdr.stopStream()

    print("")

    # Combine files
    print("Files saved: {}".format(filesSavedCount))

    #sys.exit(0)

    if filesSavedCount > 1:
        print("Combine files:")
        imgData = None
        # Add other images
        for p in range(filesSavedCount):
            fileName = "{}-{:05d}.jpg".format(imageFileName, p)
            filePath = utils.makeFilePath(outputFolder, fileName)
            img = imageProcessing.loadImage(filePath)
            if p == 0:
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

            utils.deleteFile(filePath)

        # Save result
        fileName = "{}.jpg".format(imageFileName)
        filePath = utils.makeFilePath(outputFolder, fileName)
        imgOut = imageProcessing.imageFromArray(imgData)
        imgOut.save(filePath)
        print("Done, {} saved".format(filePath))

