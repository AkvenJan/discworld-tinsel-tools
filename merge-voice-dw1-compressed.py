#!/usr/bin/env python3

import argparse
import os
import struct
import sys

# Соответствие формат → (сигнатура, расширение)
FORMATS = {
    'flac': (b'FLAC', 'flac'),
    'mp3':  (b'MP3 ', 'mp3'),
    'ogg':  (b'OGG ', 'ogg'),
}

def main():
    parser = argparse.ArgumentParser(
        prog='merge-voice.py',
        description='Merge ENGLISH-NEW.SMP and ENGLISH-NEW.IDX from original ENGLISH.IDX and compressed audio samples.',
        epilog='Script needs original ENGLISH.IDX and samples in VOICES/ folder.\n'
               'Supported formats: FLAC, MP3, OGG.\n'
               'Samples that exist in VOICES/ are written even if their IDX entry is 0.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    fmt_group = parser.add_mutually_exclusive_group(required=True)
    for name in FORMATS:
        fmt_group.add_argument(
            '-{}'.format(name), '--{}'.format(name),
            action='store_const', const=name, dest='format',
            help='Using format {} (VOICES/sample-N.{})'.format(name, FORMATS[name][1]),
        )

    args = parser.parse_args()
    fmt_name = args.format
    signature, ext = FORMATS[fmt_name]

    smpFile = open('ENGLISH-NEW.SMP', 'wb')
    idxFile = open('ENGLISH.IDX', 'rb')
    nidxFile = open('ENGLISH-NEW.IDX', 'wb')

    idxFile.seek(0, 2)
    size = idxFile.tell()
    size = size // 4
    idxCount = size
    idxFile.seek(0, 0)

    written = 4
    smpFile.write(signature)   # сигнатура в начале SMP (big-endian)
    indexNo = 0
    missing = 0
    added = 0   # count of samples added that had idx==0 originally

    while idxCount > 0:
        position = struct.unpack('<I', idxFile.read(4))[0]
        sample_no = size - idxCount
        sample_path = 'VOICES/sample-{}.{}'.format(sample_no, ext)

        if indexNo == 0:
            # Первая запись — заголовок/сигнатура, не аудио
            nidxFile.write(signature)
        elif os.path.exists(sample_path):
            with open(sample_path, 'rb') as sampleFile:
                data = sampleFile.read()
                length = len(data)
                nidxFile.write(struct.pack('<I', written))
                smpFile.write(struct.pack('<I', length))   # заголовок длины, LE
                smpFile.write(data)                         # сырые байты как есть
                written += length + 4
                if position == 0:
                    added += 1   # был нулевой в IDX, но файл добавлен
        else:
            if position != 0:
                missing += 1
            nidxFile.write(struct.pack('<I', 0))   # пустой слот — сохраняем структуру IDX

        idxCount -= 1
        indexNo += 1

    smpFile.close()
    idxFile.close()
    nidxFile.close()

    print('Ready: format={}'.format(fmt_name))
    print('  ENGLISH-NEW.SMP and ENGLISH-NEW.IDX created')
    if missing:
        print('  Error: {} samples in {} format missing in VOICES/ but were present in original IDX'.format(missing, ext))
    if added:
        print('  Added: {} samples found in VOICES/ that had zero entry in original IDX'.format(added))

if __name__ == '__main__':
    main()
