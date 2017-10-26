# Universal SDR waterfall image saver.
# (c) 2017 Dmitrii (dmitryelj@gmail.com)

import os
import ctypes
import datetime

def bold(text):
    return '\x1b[1m' + str(text) + '\x1b[0m'

def getDiskSpace():
    if isWindows():
        free_bytes = ctypes.c_ulonglong(0)
        dirname = getAppFolder()
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(dirname), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value, 0

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
  except Exception as e:
      print("deleteFile error:", str(e))

def isPhoto(filePath):
    return ".jpg" in filePath.lower() or ".png" in filePath.lower()

def datetimeFromString(s):
  # Time like "18:05" to datetime object
  t = None
  if len(s) == 5:
      now = datetime.datetime.now()
      try:
          hr  = int(s[:2])
          min = int(s[3:])
          t = now.replace(minute=min, hour=hr, second=0, microsecond=0)
          if t < now:
              t += datetime.timedelta(days=1)
      except:
          print("Options: 'tStart' parameter is invalid")
  return t

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

