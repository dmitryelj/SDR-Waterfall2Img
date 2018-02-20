import numpy as np
import utils
import optparse
import time, datetime
import imageProcessing
import sys
import re as regexp
import wave
from waveFile import WaveFile
from PIL import Image

def waterfallSaveProcess(imageWidth, imageHeight, sampleRate, frequency, outputFolder, imageFileName, dataPipe):
    try:
        savedCount = 0
        while True:
            timeout = 10
            if dataPipe.poll(timeout):
                data = dataPipe.recv()
                if len(data) == 0:
                    break
          
                now = datetime.datetime.now()
                
                # Combine all images horizontally
                h_header = imageProcessing.getHeaderHeight()
                w_total, h_total = imageWidth*len(data), h_header + imageHeight
                img_total = Image.new('RGB', (w_total, h_total))
                
                header = imageProcessing.createImageHeader(w_total, sampleRate*len(data), frequency)
                img_total.paste(header, (0,0))
                
                for index, d in enumerate(data):
                    img = imageProcessing.imageFromArray(d)
                    width, height = img.size
                    img_total.paste(img, (index*width, h_header))
                      
                fileName = "{}-{:05d}.jpg".format(imageFileName, savedCount)
                filePath = utils.makeFilePath(outputFolder, fileName)
                img_total.save(filePath)
                
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

def combineImages(imageFileName, filesSavedCount, doRemove = True):
    try:
        folder = utils.getAppFolder()
        # Combine several images to a big one
        print("Combine files:")
        imgData = None
        for p in range(filesSavedCount):
            fileName = "{}-{:05d}.jpg".format(imageFileName, p)
            filePath = utils.makeFilePath(folder, fileName)
            try:
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
            except:
                print("{} ignored".format(fileName))
    
        # Save result
        fileName = "{}.jpg".format(imageFileName)
        filePath = utils.makeFilePath(folder, fileName)
        imgOut = imageProcessing.imageFromArray(imgData)
        imgOut.save(filePath)
        print("Done, {} saved".format(filePath))
        
        if doRemove is False: return

        # Remove originals
        for p in range(filesSavedCount):
            fileName = "{}-{:05d}.jpg".format(imageFileName, p)
            filePath = utils.makeFilePath(folder, fileName)
            utils.deleteFile(filePath)

    except Exception as e:
        exc_type, exc_obj, tb = sys.exc_info()
        print("combineImages error:", e.args[0], tb.tb_lineno)

def iqSaveProcess(dataFile, dataPipe):
    try:
        savedCount = 0
        while True:
            if dataPipe.poll():
                data = dataPipe.recv()
                if len(data) == 0:
                    break
            
                #data_ = data #data.astype('int16')
                #data1 = np.zeros(2*len(data), dtype='int16')
                #dataR = data.real * 4096
                #dataI = data.imag * 4096
                #data2 = np.append(dataR.astype('int16'), dataI.astype('int16'))
                #for p in range(len(data)):
                #    data1[2*p]   = dataR[p]
                #    data1[2*p+1] = dataI[p]
                #data2 = data.astype('complex64')
                
                #print("Save:", len(data), type(data), type(data[0]))
                
                fileName = "{}-{:05d}.iq".format(dataFile, savedCount)
                #dataR.tofile(fileName)
                #fileName = "{}-{:05d}.q".format(dataFile, savedCount)
                data.tofile(fileName)
                
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

def combineIQData(fileName, iqSavedCount, sampleRate, bps):
    fileOutput = "{}.wav".format(fileName)

    for p in range(iqSavedCount):
        fileInput = "{}-{:05d}.iq".format(fileName, p)

        try:
            file = open(fileInput, "rb")
            if bps == 8:
                data = np.fromfile(file, dtype=np.int8)
                fileData = data.astype('int16')
                fileData *= 32
            else:
                fileData = np.fromfile(file, dtype=np.int16)
                #fileData.byteswap(True)
                #fileData = fileData.byteswap().newbyteorder()
                #fileData = data.astype('int16')
                #print("D", type(fileData[0]), len(fileData))
                #for d in range(len(fileData)/2):
                #    v = fileData[2*d]
                #    fileData[2*d] = fileData[2*d+1]
                #    fileData[2*d+1] = v
            file.close()
    
            if p % 100 == 0:
                print("Combine chunks: {} of {}".format(p+1, iqSavedCount))

            if p == 0:
                # Create new file
                with open(fileOutput, "wb") as fileNew:
                    cnt = len(fileData)
                    w = WaveFile(sample_rate=sampleRate, samples_num=cnt*iqSavedCount)
                    w.saveHeader(fileNew)
                    fileNew.write(fileData)
            else:
                # Append to the end
                with open(fileOutput, "ab") as fileAppend:
                    fileAppend.write(fileData)

            utils.deleteFile(fileInput)
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            print("combineIQData error:", str(e), e.args[0], tb.tb_lineno)
          
    print("Done")

def waveToSpectrum(fileInput, fileOutput, imageWidth, average):
    wav = wave.open(fileInput, "r")
    nchannels = wav.getnchannels()
    nframes   = wav.getnframes()
    sampleRate = wav.getframerate()
    sampwidth = wav.getsampwidth()
    frequency = 100000000
    
    # Extract frequency from the filename: HDSDR_20171019_164248Z_100000kHz_RF
    m = regexp.search('_([0-9]+)kHz', fileInput, regexp.IGNORECASE)
    if m:
        found = m.group(1)
        frequency = 1000*int(found)
    
    print("Channels:", nchannels)
    print("Sample rate:", sampleRate)
    print("Samples:", nframes)
    print("Bytes per sample:", sampwidth)
    print("Central frequency:", frequency)
    if sampwidth != 2 or nchannels != 2:
        print("Only 16-bit stereo files are supported in this version")
        return

    print("")
    print("Converting...")

    # Get wav data, convert to FFT
    fftLines = []
    block_size = imageWidth
    dataMovingBlock = np.zeros(imageWidth)
    for p in range(int(nframes/(block_size*nchannels*average))):
        fftData = np.zeros(imageWidth)
        for v in range(average):
            # Read samples
            frames = wav.readframes(imageWidth)
            data = np.fromstring(frames, np.int32)
            if len(data) < imageWidth:
                break

            # 2x16bit => I + Q
            data = data[:imageWidth]
            dataForFFT = data[0:imageWidth].astype('uint32')
            re = dataForFFT & 0xFFFF
            im = dataForFFT >> 16
            dataC = np.asfarray(re) + 1j*np.asfarray(im)
            
            # Get FFT
            fft = imageProcessing.applyFFT(dataC, imageWidth)
            fftData += fft
        
        fftData /= average
        fftLine = imageProcessing.generateNewLine(imageWidth, fftData, iqBPS=sampwidth*8)
        fftLines.append(fftLine)
        
        if len(fftLines) % 100 == 0:
            print("{} lines added".format(len(fftLines)))

        if len(fftLines) > 16384:
            print("Warning: image too big, stopped. Use 'average' parameter to reduce the size.")
            break

    # Save to image
    img = imageProcessing.createImageHeader(imageWidth, sampleRate, frequency)
    imgData = imageProcessing.imageToArray(img)
    imgDataOut = np.append(imgData, fftLines, axis=0)

    # fileName = fileOutput #"{}-{:05d}.jpg".format(imageFileName, savedCount)
    # filePath = utils.makeFilePath(utils.getAppFolder(), fileName)
    imgOut = imageProcessing.imageFromArray(imgDataOut)
    imgOut.save(fileOutput)
    print("Blocks saved:", len(fftLines))

if __name__ == '__main__':
    printIntro()
    
    parser = optparse.OptionParser()
    parser.add_option("--file", dest="fileName", help="file name", default="")
    parser.add_option("--delete", dest="doDelete", help="delete files after processing", default="")
    options, args = parser.parse_args()
    
    fileName = options.fileName
    doRemove = options.doDelete == 'true' or options.doDelete == '1'

    if len(fileName) == 0:
        sys.exit(0)

    # 2017-09-14-14-54-07-101000000-00000.jpg -> # 2017-09-14-14-54-07-101000000-00000
    fileName = utils.getFileNameOnly(fileName)
    # 2017-09-14-14-54-07-101000000-00000 -> 2017-09-14-14-54-07-101000000
    posIndex = fileName.rfind('-')
    filePattern = fileName[0:fileName.rfind('-')]

    print("Image pattern: ", filePattern)

    folder = utils.getAppFolder()
    files = utils.getImagesList(folder)

    filesFiltered = list(filter(lambda f: filePattern + "-" in f, files))
    print("Images found:", len(filesFiltered))

    print("Processing...")
    combineImages(filePattern, len(filesFiltered), doRemove = doRemove)

    print("")

