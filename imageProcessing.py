# Universal SDR waterfall image saver.
# (c) 2017 Dmitrii (dmitryelj@gmail.com)

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import os, sys, time
import utils

headerH = 20

def getImageSize(img):
    return img.size

def getHeaderHeight():
    return headerH

def createImageHeader(imageWidth, sampleRate, frequencyKHz):
  try:
    img = Image.new('RGB', (imageWidth, headerH))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default() # ImageFont.truetype("sans-serif.ttf", 12)
    
    step = 500000
    fft = imageWidth
    tickW = step*fft/sampleRate
    middleX = imageWidth/2
    cnt = int(sampleRate/step)

    # Marks
    for p in range(-5*cnt, 5*cnt+1):
      x = middleX + p*tickW/5
      draw.line((x,headerH-5, x,headerH), fill=(200,200,200))

    # Labels
    step = 500000
    middleX = imageWidth/2
    cnt = int(sampleRate/step)
    if cnt == 0: cnt = 1
    for p in range(-cnt, cnt+1):
      x = middleX + p*tickW
      freqKHz = frequencyKHz + p*step
      freqStr = str(freqKHz/1000)
      w, h = draw.textsize(freqStr)
      text_x = x - w/2
      draw.text((text_x, 3), freqStr, font=font, fill=(200,200,200))

    # Bottom divider
    draw.line((0,headerH-1, imageWidth,headerH-1), fill=(200,200,200))
    return img
  except Exception as e:
    exc_type, exc_obj, tb = sys.exc_info()
    print("createImageHeader error:", e.args[0], tb.tb_lineno)
    return None

def loadImage(fileName):
    return Image.open(fileName)

def imageFromArray(data):
    return Image.fromarray(np.uint8(data), 'RGB')

def imageToArray(img):
    return np.array(img)

def generateNewLine(imageWidth, data):
    paletteR, paletteG, paletteB = 4, 1, 4
    k = 16
    def convert(val):
      v = val if val < 255 else 255
      return [v/paletteR, v/paletteG, v/paletteB]

    # Reverce array parts (high frequency - right part)
    partsLR = np.split((data*k).astype(int), 2)
    pts1 = [convert(pt) for pt in partsLR[1]]
    pts2 = [convert(pt) for pt in partsLR[0]]    
    return np.array(pts1 + pts2)

def applyFFT(rawData, imageWidth):
    rawFFt = np.fft.fft(rawData, n = imageWidth) #,norm="ortho")
    rawAbs = np.absolute(rawFFt)
    return rawAbs
