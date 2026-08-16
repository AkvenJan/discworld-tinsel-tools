#!/usr/bin/env python3

import struct

smpFile = open('ENGLISH-NEW.SMP', 'wb')
idxFile = open('ENGLISH.IDX', 'rb')
nidxFile = open('ENGLISH-NEW.IDX', 'wb')

count = 0
idxFile.seek(0, 2)
size = idxFile.tell()
size = size // 4
idxCount = size
idxFile.seek(0, 0)
written = 4
smpFile.write(b'FLAC')
while idxCount > 0:
    position = struct.unpack('<I', idxFile.read(4))[0]
    if position == 0:
        nidxFile.write(struct.pack('<I', 0))
        # written += 4
    else:
        with open('VOICES/sample-{}.flac'.format(size - idxCount), 'rb') as flacFile:
            flac_data = flacFile.read()
            length = len(flac_data)
            nidxFile.write(struct.pack('<I', written))
            smpFile.write(struct.pack('<I', length))   # заголовок длины, LE — теперь нужен
            smpFile.write(flac_data)                    # сырые байты FLAC как есть
            written += length + 4
    idxCount -= 1

smpFile.close()
idxFile.close()
nidxFile.close()