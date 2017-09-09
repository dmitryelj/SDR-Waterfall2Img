# Universal SDR waterfall image saver.
# (c) 2017 Dmitrii (dmitryelj@gmail.com)

from wf2img import SDR
import wf2img
import utils

if __name__ == '__main__':
    print(utils.bold("SDR Waterfall2Img version " + wf2img.getVersion()))

    sdr = SDR()
    # List all connected SoapySDR devices
    devices = sdr.listDevices()
    print("Receivers found:", len(devices))

    print("---")
    for d in devices:
        sdr.initDevice(driverName = d['driver'])
        print("Name:", d['driver'])
        print("Description:", d['label'])
        print("Gains:", sdr.getGains())
        print("Sample rates:")
        print(sdr.getSampleRates())
        print("")
