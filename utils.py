# Universal SDR waterfall image saver.
# (c) 2017 Dmitrii (dmitryelj@gmail.com)

import os

def bold(text):
    return '\x1b[1m' + str(text) + '\x1b[0m'

def getDiskSpace():
    st = os.statvfs('/')
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    return free,total

def isFileExist(filePath):
    return os.path.isfile(filePath)

def getFileName(filePath):
    return os.path.splitext(filePath)[0]

def getFileNameOnly(filePath):
    path, file = os.path.split(filePath)
    fileExt = os.path.splitext(file)[0]
    return fileExt

def getFileExtention(filePath):
    path, file = os.path.split(filePath)
    fileExt = os.path.splitext(file)[1]
    return fileExt


def deleteFile(filePath):
  try:
      os.remove(filePath)
  except:
      pass

def isPhoto(filePath):
    return ".jpg" in filePath.lower() or ".png" in filePath.lower()

def getImagesList(folder):
    # Get all files in a folder and subfolders
    file_paths = []
    try:
      for root, directories, files in os.walk(folder):
        for filename in files:
          if isPhoto(filename):
            # Save full file path
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    except:
      pass
    
    return file_paths

def getAppFolder():
  return os.path.dirname(os.path.realpath(__file__))

def makeFilePath(folder, file):
  return folder + os.sep + file

def isWindows():
  return os.name == "nt"

def isRaspberryPi():
  return os.name != "nt" and os.uname()[0] == "Linux"

