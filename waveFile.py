import struct

class WaveFile(object):

    def __init__(self, sample_rate, samples_num, bits_per_sample=16):
        self.subchunk_size = 16		# subchunk data size (16 for PCM)
        self.compression_type = 1	# compression (PCM = 1 [linear quantization])
        self.channels_num = 2		# channels (mono = 1, stereo = 2)
        self.bits_per_sample = int(bits_per_sample)
        self.block_alignment = int(self.channels_num * self.bits_per_sample / 8)
        self.sample_rate = int(sample_rate)
        self.samples_num = int(samples_num)
        self.byte_rate = int(self.sample_rate * self.channels_num * self.bits_per_sample / 8)
        self.duration = int(samples_num/self.sample_rate)
        self.data = []

    def add_data_subchunk(self, duration, data):
        self.duration += duration
        self.data += data

    def saveHeader(self, f):
        self.subchunk2_size = int(self.samples_num * self.channels_num * self.bits_per_sample / 8)
        
        # write RIFF header
        f.write('RIFF'.encode('utf-8'))
        f.write(struct.pack('<i', 4 + (8 + self.subchunk_size) + (8 + self.subchunk2_size)))
        f.write('WAVE'.encode('utf-8'))
        # write fmt subchunk
        f.write('fmt '.encode('utf-8'))										# chunk type
        f.write(struct.pack('<i', self.subchunk_size))		# data size
        f.write(struct.pack('<h', self.compression_type))	# compression type
        f.write(struct.pack('<h', self.channels_num))		# channels
        f.write(struct.pack('<i', self.sample_rate))		# sample rate
        f.write(struct.pack('<i', self.byte_rate))			# byte rate
        f.write(struct.pack('<h', self.block_alignment))	# block alignment
        f.write(struct.pack('<h', self.bits_per_sample))	# sample depth
        # write data subchunk
        f.write('data'.encode('utf-8'))
        f.write(struct.pack ('<i', self.subchunk2_size))
        for d in self.data:
            sound_data = struct.pack('<h', d)
            f.write(sound_data)

