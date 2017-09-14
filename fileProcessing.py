import numpy as np
import utils
import optparse
from wf2img import *

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
          
            data_ = data.astype('int32')
            
            print("Save:", len(data_), type(data_), type(data_[0]))
            
            fileName = "{}-{:05d}.iq".format(dataFile, savedCount)
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

