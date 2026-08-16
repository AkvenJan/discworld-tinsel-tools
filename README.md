# Discworld Tools
Scripts and utilities for Discworld games based on Tinsel engine

Forked from https://github.com/adventurebrew/kolminey

I needed to modify tools to support PSX version of Discworld 1 game

## Audio formats

| Version        | Format                          | Sample rate | Channels | Decodes to               |
|----------------|---------------------------------|-------------|----------|--------------------------|
| Discworld 1 PC | Raw 8-bit unsigned PCM          | 22050 Hz    | mono     | 8-bit 22050 Hz WAV       |
| Discworld 1 PSX| XA-ADPCM 4-bit (Sony SPU)       | 44100 Hz    | mono     | 16-bit 44100 Hz WAV      |
| Discworld 2 PC | Tinsel ADPCM 6-bit (custom)     | 22050 Hz    | mono     | 16-bit 22050 Hz WAV      |

The PSX version stores voice samples as Sony XA-ADPCM inside `ENGLISH.SMP`, indexed by `ENGLISH.IDX`. The PC version stores the same samples as raw 8-bit unsigned PCM. Both are unpacked to standard WAV files.

## Scripts

### `split-text.py`

Parses `english.txt` — the game's text resource for both PC and PSX versions — into a plain-text file with one line per speech line, prefixed by the actor/speaker number:

```
0 "So what happened?"
0 "Nothing! Nothing happened!
That's just the point."
1 "Steal? Now do I look like a thief?"
1 "My stick! They all want my magic stick!"
```

The speaker index corresponds to the voice sample referenced by the same line in the script data, so the output can be matched against the extracted `.wav` files.

### `split-voice-dw1-pc.py`

Unpacks voice samples from the **PC** version of Discworld 1.

- Reads `ENGLISH.IDX` as an array of little-endian `DWORD` offsets.
- For each non-zero offset, seeks into `ENGLISH.SMP`, reads the 4-byte sample length, then the raw 8-bit unsigned PCM data.
- Writes each sample to `VOICES/sample-N.wav` (22050 Hz, mono, 8-bit).

### `split-voice-dw1-psx.py`

Unpacks voice samples from the **PSX** version of Discworld 1.

- Reads `ENGLISH.IDX` as an array of little-endian `DWORD` offsets.
- For each non-zero offset, seeks into `ENGLISH.SMP`, reads the 4-byte sample length, then the XA-ADPCM data.
- Decodes each 16-byte XA-ADPCM block (filter + shift header, 28 nibble samples, double-precision prediction) into 16-bit signed PCM.
- Writes each sample to `VOICES/sample-N.wav` (44100 Hz, mono, 16-bit).

The XA-ADPCM decoder follows the same algorithm as ScummVM's`audio/decoders/xa.cpp` (`Audio::makeXAStream`), which is the path used by the Tinsel engine for `TinselV1PSX` in `engines/tinsel/sound.cpp`.