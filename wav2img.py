# Universal SDR IQ/waterfall image saver.
# (c) 2017 Dmitrii (dmitryelj@gmail.com)

import logging
import optparse
import utils
import imageProcessing
import fileProcessing
import sys
from version import *

if __name__ == '__main__':
    print(utils.bold('SDR Wav2Img '+ getVersion()))

    parser = optparse.OptionParser()
    parser.add_option("--input", dest="fileInput", help="WAV file name", default="")
    parser.add_option("--output", dest="fileOutput", help="Image file name", default="")
    parser.add_option("--imagewidth", dest="imagewidth", help="image width", default=1024)
    parser.add_option("--average", dest="average", help="FFT average", default=1)
    options, args = parser.parse_args()

    fileInput = options.fileInput
    if len(fileInput) == 0:
        print("Run 'python3 wav2img.py --input=file.wav [--output=file.jpg] [--imagewidth=1024] [--average=1]'")
        sys.exit(0)
    
    fileOutput = options.fileOutput if len(options.fileOutput) > 0 else fileInput.replace(".wav", ".jpg")
    imageWidth = int(options.imagewidth)
    average    = int(options.average)
    
    print("Convert {} to {}".format(fileInput, fileOutput))
    print("Image width:", imageWidth)
    print("Average:", average)
    
    fileProcessing.waveToSpectrum(fileInput, fileOutput, imageWidth, average)

    print("Done")
    print("")
