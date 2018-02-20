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
import math
import optparse
import datetime
import imageProcessing
import fileProcessing
import utils
import logging
from sdr import SDR
from version import *
if utils.isRaspberryPi():
    import libTFT

def printIntro():
    print(utils.bold('SDR Waterfall2Img, version %s\n' % getVersion()))
    print(utils.bold('Usage: python3 wf2img.py  --f=frequency [--fStart=f1 --fEnd=f2] [--sr=sampleRate] [--sdr=receiver] [--imagewidth=imageWidth] [--imagefile=fileName] [--average=N] [--saveIQ=1] [--tStart=18:30] [--tLimit=120] [--batch="frequency;timeStart;timeEnd"]'))
    print("Run 'nohup <python3 wf2img.py parameters> &' to execute in the background")
    print("To combine files, saved before, use: python3 fileProcessing.py --file=fileName.jpg [--delete=true]")
    print("")

if __name__ == '__main__':
    printIntro()
    
    if sys.version_info[0] < 3:
        print("Error: Python3 is required, use 'python3 wf2img.py' to run the script\n")
        sys.exit(1)

    # Command line arguments
    parser = optparse.OptionParser()
    parser.add_option("--sdr", dest="sdr", help="receiver name", default="")
    parser.add_option("--sdrgain", dest="sdrgain", help="sdr gain settings", default="")
    parser.add_option("--sr", dest="samplerate", help="sample rate", default=2000000)
    parser.add_option("--bw", dest="bandwidth", help="bandwidth", default=0)
    parser.add_option("--f", dest="frequency", help="center frequency", default=101000000)
    parser.add_option("--fStart", dest="frequency_start", help="center frequency", default=0)
    parser.add_option("--fEnd", dest="frequency_end", help="center frequency", default=0)
    parser.add_option("--imagewidth", dest="imagewidth", help="image width", default=1024)
    parser.add_option("--average", dest="average", help="stream average", default=16)
    parser.add_option("--markerS", dest="markerInS", help="time marker in seconds", default=60)
    parser.add_option("--saveIQ", dest="saveIQ", help="save IQ in HDSDR-compatible wav file", default="false")
    parser.add_option("--saveWaterfall", dest="saveWaterfall", help="save waterfall", default="true")
    parser.add_option("--tStart", dest="timeStart", help="app start recording time", default="")
    parser.add_option("--tEnd",   dest="timeEnd",   help="app end recording time", default="")
    parser.add_option("--tLimit", dest="timeLimit", help="app run time limit in seconds", default=9999999)
    parser.add_option("--decimation", dest="decimation", help="signal decimation", default=1)
    parser.add_option("--batch", dest="batch", help="batch job (in format frequency1;time1-1;time1-2;frequency2;time2-1;time2-2)", default="")
    parser.add_option("--debug", dest="debug", help="debug simulation", default="")
    options, args = parser.parse_args()
    
    sampleRate = int(options.samplerate)
    bandwidth = int(options.bandwidth)
    wavFileName = ""
    imageWidth = imageProcessing.getNearestImageWidth(int(options.imagewidth))
    average = int(options.average)
    decimation = int(options.decimation)
    markerInS = int(options.markerInS)
    markerRGB = [220,0,0]
    imageHeightLimit = 16384    # Not used yet
    saveWaterfall = isinstance(options.saveWaterfall, str) and (options.saveWaterfall == 'true' or options.saveWaterfall == '1' or options.saveWaterfall == 'True')
    saveIQ = isinstance(options.saveIQ, str) and (options.saveIQ == 'true' or options.saveIQ == '1' or options.saveIQ == 'True')
    useDebug = isinstance(options.debug, str) and (options.debug == 'true' or options.debug == '1' or options.debug == 'True')
    outputFolder = utils.getAppFolder()
    frequencies = [ int(options.frequency) ]
    timesStart = [ utils.datetimeFromString(options.timeStart) ]
    timesEnd   = [ utils.datetimeFromString(options.timeEnd) ]
    timesLimit = [ int(options.timeLimit) ]
    # Batch job (optional)
    if len(options.batch) > 10:
        # Sample format: 110000000;15:55;15:57;120000000;16:00;16:05
        print("Found batch tasks:", options.batch)
        items = options.batch.split(";")
        if len(items) % 3 == 0:
            frequencies = []
            timesStart = []
            timesEnd = []
            for p in range(int(len(items)/3)):
                frequency = items[3*p]
                ts = items[3*p + 1]
                te = items[3*p + 2]
                
                tsDate = utils.datetimeFromString(ts)
                teDate = utils.datetimeFromString(te)
                if tsDate is None or teDate is None: continue
                
                print("Batch added: f={}, start:{}, end:{}".format(int(frequency), tsDate, teDate))
                frequencies.append(int(frequency))
                timesStart.append(tsDate)
                timesEnd.append(teDate)
        else:
            print("Incorrect batch format, should be 'frequency;time1;time2'")
    # Frequency span (optional)
    frequency_start = 0
    frequency_end = 0
    frequency_step = sampleRate
    frequency_steps = 1
    if int(options.frequency_start) != 0 and int(options.frequency_end) != 0 and saveIQ is False:
        frequency_start = int(options.frequency_start)
        frequency_steps = int(math.ceil((int(options.frequency_end) - int(options.frequency_start))/frequency_step))
        frequency_end = frequency_start + frequency_step*frequency_steps
        frequencies = [ frequency_start + int(frequency_step*frequency_steps/2) ]

    sdr = SDR()
    # List all connected SoapySDR devices
    devices = sdr.listDevices()
    print("Receivers found:")
    for d in devices:
        print(d)
    print("")

    device = options.sdr if len(options.sdr) > 0 else sdr.findSoapyDevice(devices)
    print("Receiver selected:", device)
    print("")
    
    if device is None and len(options.sdr) > 0 and useDebug is False:
        print("Error: receiver not found")
        sys.exit(1)
    if device is None and useDebug is False:
        print("Error: no receiver detected")
        sys.exit(1)
    if saveIQ is False and saveWaterfall is False:
        print("Error: no task selected, saveIQ and saveWaterfall are both false")
        sys.exit(1)

    sdr.initDevice(device)
    sdr.setSampleRate(sampleRate)
    if bandwidth != 0:
        sdr.setBandwidth(bandwidth)
    if len(options.sdrgain) > 0:
        sdr.setGainFromString(options.sdrgain)
    else:
        if device == 'sdrplay':
            sdr.setGainFromString("IFGR:40;RFGR:4")
        if device == 'rtlsdr':
            sdr.setGainFromString("TUNER:30")

    print("Receiver:", device)
    print("Sample rate:", sampleRate)
    if frequency_steps > 1:
        print("Frequency span: {}..{}, step {}".format(frequency_start, frequency_end, frequency_step))
    else:
        print("Frequencies:", frequencies)
        print("Frequency span: disabled")
    print("Sample rates:", sdr.getSampleRates())
    print("Bandwidth:", bandwidth if bandwidth != 0 else "default")
    print("Bandwidths:", sdr.getBandwidths())
    print("BPS:", sdr.getBps())
    print("Gains:", sdr.getGains())
    print("Average, blocks:", average)
    print("Vertical markers (s):", markerInS)
    print("Output folder:", outputFolder)
    print("Save waterfall:", saveWaterfall)
    print("Save IQ:", saveIQ)
    print("")

    for index, frequency in enumerate(frequencies):
        # Initialize SDR device
        sdr.setCenterFrequency(frequency)
        sdr.startStream()
        
        timeStart = timesStart[index] if index < len(timesStart) else None
        timeEnd = timesEnd[index] if index < len(timesEnd) else None
        timeLimit = timesLimit[index] if index < len(timesLimit) else 9999999

        # Show status
        print(utils.bold("Task {} of {}".format(index+1, len(frequencies))))
        print("Start time:", "-" if timeStart is None else timeStart)
        print("End time:", "-" if timeEnd is None else timeEnd)
        print("Limit in seconds:", "-" if timeLimit == 9999999 else timeLimit)
        print("")

        # Wait for the start
        if timeStart is not None:
            while True:
                now = datetime.datetime.now()
                diff = int((timeStart - now).total_seconds())
                print("{:02d}:{:02d}:{:02d}: Recording will be started after {}m {:02d}s...".format(now.hour, now.minute, now.second, int(diff/60), diff%60))
                time.sleep(1)
                if diff <= 1: break
        else:
            print("Recording will be started after 4 seconds...")
            time.sleep(4)
        print("")

        print("Recording started, press Ctrl+C to stop")

        # Output name from current time
        dtStr = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        imageFileName = "{}-{}".format(dtStr, frequency)
        if frequency_steps > 1:
            imageFileName = "{}-{}-{}".format(dtStr, frequency_start, frequency_end)
        # Wav file name, like "HDSDR_20171002_191902Z_7603kHz_RF.wav"
        if saveIQ:
            dtStr = datetime.datetime.now().strftime("%Y%m%d_%H%M%SZ")
            wavFileName = "HDSDR_{}_{}kHz_RF".format(dtStr, int(frequency/1000))

        # Image data
        imgBlockSize = 32
        imgBlockNumber = 0
        imgBlockCombine = 2
        filesSavedCount = 0
        iqSavedCount = 0
        iqSavedSize = 0
        iqBPS = sdr.getBps()
        
        # Start saving waterfall process
        parentPipe, childPipe = multiprocessing.Pipe()
        params = [ imageWidth, imgBlockSize, int(sampleRate/decimation), frequency, outputFolder, imageFileName, parentPipe ]
        process = multiprocessing.Process(target=fileProcessing.waterfallSaveProcess, args=params)
        process.start()
        
        # Start saving file process
        iqParentPipe, iqChildPipe = multiprocessing.Pipe()
        paramsIQ = [ wavFileName, iqParentPipe ]
        processIQ = multiprocessing.Process(target=fileProcessing.iqSaveProcess, args=paramsIQ)
        processIQ.start()

        start = datetime.datetime.now()
        timeInS = 24*60*start.hour + 60*start.minute + start.second
        diffInS = timeInS - markerInS*int(timeInS/markerInS)
        timeMarker = start - datetime.timedelta(seconds=diffInS)
        
        class TimeOver(Exception): pass
        class FreeSpaceError(Exception): pass

        try:
            # Array of lines for each frequency step
            samplesToAdd = [[] for i in range(frequency_steps)]
            while True:
                for freq_index in range(frequency_steps):
                    # Set span frequency (optional)
                    if frequency_steps > 1:
                        cur_freq = frequency_start + freq_index*frequency_step + frequency_step/2
                        # print("Freq:", cur_freq)
                        sdr.setCenterFrequency(cur_freq)
                        # Skip first data (needs time to set proper frequency)
                        sdr.readStream() 
                        sdr.readStream()
                
                    fftData = np.zeros(imageWidth)
                    # Get data
                    for p in range(average):
                        data, dataLen = sdr.readStream()
                        if dataLen > 0:
                            # Decimation (optional)
                            if decimation > 1:
                                data = data[::decimation]   # data = data.reshape(-1, decimation).mean(axis=1)
                                dataLen = int(dataLen/decimation)
                            # Save IQ
                            if saveIQ:
                                iqChildPipe.send(data[0:dataLen])
                                iqSavedCount += 1
                                iqSavedSize += dataLen*2*iqBPS/8 # I+Q data in array
                            # Save FFT
                            if saveWaterfall:
                                dataC = None
                                if iqBPS == 8:
                                    # 2x8bit => I + Q
                                    dataForFFT = data[0:imageWidth].astype('uint16')
                                    re = dataForFFT & 0xFF
                                    im = dataForFFT >> 8
                                    dataC =  np.asfarray(re) + 1j*np.asfarray(im)
                                else:
                                    # 2x16bit => I + Q
                                    dataForFFT = data[0:imageWidth].astype('uint32')
                                    re = dataForFFT & 0xFFFF
                                    im = dataForFFT >> 16
                                    dataC = np.asfarray(re) + 1j*np.asfarray(im)

                                fft = imageProcessing.applyFFT(dataC, imageWidth)
                                # Suppress DC
                                fft[0] = fft[1]
                                fftData += fft

                                #print("FFT", len(fft))
                    fftData /= average

                    now = datetime.datetime.now()
                    # Check run time
                    runTime = int((now - start).total_seconds())
                    if runTime > timeLimit:
                        raise TimeOver
                    if timeEnd is not None and now > timeEnd:
                        raise TimeOver
                    # Check free space
                    free,total = utils.getDiskSpace()
                    if free < 64*1024*1024:
                        raise FreeSpaceError

                    if saveWaterfall:
                        imgLine = imageProcessing.generateNewLine(imageWidth, fftData, iqBPS)
                        # Add time marker
                        diffInS = (now - timeMarker).total_seconds()
                        if diffInS > markerInS:
                            for x in range(10):
                              imgLine[x] = markerRGB
                            timeMarker = now
                        # print("Line added", freq_index)
                        samplesToAdd[freq_index].append(imgLine)
        
                # print("Block added", len(samplesToAdd[0]))
                # Save data, if ready
                if len(samplesToAdd[0]) == imgBlockSize:
                    childPipe.send(samplesToAdd)
                    
                    samplesToAdd = [[] for i in range(frequency_steps)]
                    filesSavedCount += 1

                # Notify if IQ save active
                if saveIQ and iqSavedCount % 64 == 0:
                    print("{}:{:02d}s: {}.wav: {}Mb saved, {}Mb free on device".format(int(runTime/60), runTime%60, imageFileName, int(iqSavedSize/(1024*1024)), int(free/(1024*1024))))

        except KeyboardInterrupt:
            pass
        except FreeSpaceError:
            print("Error: no free space on device, recording stopped")
        except TimeOver:
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

        # sys.exit(0)

        # Combine files
        print("Images saved: {}".format(filesSavedCount))
        print("IQ blocks saved: {}".format(iqSavedCount))

        if filesSavedCount > 1:
            fileProcessing.combineImages(imageFileName, filesSavedCount)
        if iqSavedCount > 0:
            fileProcessing.combineIQData(wavFileName, iqSavedCount, int(sampleRate/decimation), iqBPS)

        print("")


