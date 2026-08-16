#!/usr/bin/env python3

import os, struct, wave

XA_FILTERS = [
    (0.0,        0.0),
    (60.0/64.0,  0.0),
    (115.0/64.0, -52.0/64.0),
    (98.0/64.0,  -55.0/64.0),
    (122.0/64.0, -60.0/64.0),
]

def decode_xa_adpcm(data):
    samples = []
    pos = 0
    s1 = s2 = 0.0  # double precision, как в xa.cpp
    loop_point = 0
    end_of_data = False

    while not end_of_data and pos + 16 <= len(data):
        b0 = data[pos]
        shift = b0 & 0x0F            # младший полубайт — масштаб
        predictor = (b0 >> 4) & 0xF  # старший полубайт — фильтр (0–4)
        flags = data[pos + 1]
        pos += 2

        if flags == 3:               # Loop
            pos = loop_point; s1 = s2 = 0.0; continue
        elif flags == 6:             # Set loop point
            loop_point = pos - 2
        elif flags == 7:             # End of stream
            end_of_data = True; break

        raw = [0.0] * 28
        for i in range(0, 28, 2):
            d = data[pos]; pos += 1
            s = (d & 0x0F) << 12
            if s & 0x8000: s -= 0x10000
            raw[i] = float(s >> shift)
            s = (d & 0xF0) << 8
            if s & 0x8000: s -= 0x10000
            raw[i + 1] = float(s >> shift)

        for i in range(28):
            raw[i] += s1 * XA_FILTERS[predictor][0] + s2 * XA_FILTERS[predictor][1]
            s2 = s1; s1 = raw[i]
            v = int(raw[i] + 0.5)
            samples.append(max(-32768, min(32767, v)))

    return samples

def main():
    smp_file = open('ENGLISH.SMP', 'rb')
    idx_file = open('ENGLISH.IDX', 'rb')
    os.makedirs('VOICES', exist_ok=True)

    idx_file.seek(0, 2)
    idx_size = idx_file.tell()
    idx_count = idx_size // 4
    idx_file.seek(0, 0)

    total = idx_count
    extracted = 0

    while idx_count > 0:
        position = struct.unpack('<I', idx_file.read(4))[0]
        idx_count -= 1
        if position == 0:
            continue

        smp_file.seek(position, 0)
        sample_size = struct.unpack('<I', smp_file.read(4))[0]
        raw_data = smp_file.read(sample_size)

        samples = decode_xa_adpcm(raw_data)
        if not samples:
            continue

        sample_num = total - idx_count
        out_path = os.path.join('VOICES', 'sample-{}.wav'.format(sample_num - 1))
        with wave.open(out_path, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
        extracted += 1

    smp_file.close()
    idx_file.close()
    print('Ready: {} samples > VOICES/ (44100 Hz, mono, 16-bit)'.format(extracted))

if __name__ == '__main__':
    main()