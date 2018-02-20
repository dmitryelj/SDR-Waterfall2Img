# SDR soapy wrapper
# (c) 2017 Dmitrii (dmitryelj@gmail.com)

import numpy as np
import os, sys, time
try:
    if __import__('imp').find_module('SoapyDevice')[1] is not None:
        from soapyDevice import SoapyDevice
except:
    pass

class SDR(object):
    def __init__(self):
        self.isInit = False
        self.sdr = None
        self.name = ""
        # For debug/simulation only
        self.fakeName = "fake"
        self.fakeSampleRate = 1000000

    def listDevices(self):
        try:
            return SoapyDevice.listDevices()
        except:
            return []

    def initDevice(self, name = None, driverName = None):
        if name is None and driverName is None:
            self.name = self.fakeName
            return

        # Search by additional parameter, like 'driver=rtlsdr,rtl=1'
        if name is not None and ',' in name:
            self.sdr = SoapyDevice(name)
            self.name = name
            return

        # Search by driver
        if driverName is not None:
            self.sdr = SoapyDevice('driver=' + driverName)
            self.name = driverName
            return

        # Search by driver or description
        devices = self.listDevices()
        for d in devices:
            driver = d['driver']
            description = d['label']
            if name == driver or name in description:
                self.sdr = SoapyDevice('driver=' + driver)
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
            return [self.fakeSampleRate]
        
        return self.sdr.list_sample_rates()

    def getBandwidths(self):
        if self.sdr is None:
            return []

        return self.sdr.list_bandwidths()

    def getBps(self):
        if 'rtlsdr' in self.name or 'hackrf' in self.name:
            return 8
        return 16

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
            try:
                self.sdr.set_gain(name, float(value))
            except:
                print("Warning: cannot set gain {} to {}".format(name, value))

    def setSampleRate(self, samplerate):
        if self.sdr is not None:
            self.sdr.sample_rate = samplerate
        else:
            self.fakeSampleRate = samplerate

    def setBandwidth(self, bandwidth):
        if self.sdr is not None:
            self.sdr.bandwidth = bandwidth

    def setCenterFrequency(self, frequency):
        if self.sdr is not None:
            self.sdr.freq = frequency

    def startStream(self):
        if self.sdr is not None:
          # Setup base buffer and start receiving samples. Base buffer size is determined
          # by SoapySDR.Device.getStreamMTU(). If getStreamMTU() is not implemented by driver,
          # SoapyDevice.default_buffer_size is used instead
          self.sdr.start_stream(buffer_size=65536)

    def stopStream(self):
        if self.sdr is not None:
            self.sdr.stop_stream()

    def readStream(self):
        if self.sdr is not None:
            res = self.sdr.read_stream()
            dataLen = res.ret
            #print("Data received", len(res))
            return self.sdr.buffer if res.ret > 0 else [], dataLen
        else:
            randData = np.random.rand(4096)
            randData *= 32768
            randData -= 16384
            time.sleep(0.01)
            return randData.astype('int16'), len(randData)

if __name__ == '__main__':
    pass

