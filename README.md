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

### `merge-voice-dw1-wav.py`

Reassembles a new `ENGLISH-NEW.SMP` from the original `ENGLISH.IDX` and a set of WAV files in `VOICES/` folder.

- Reads `ENGLISH.IDX` as an array of little-endian `DWORD` offsets.
- For each non-zero entry, opens `VOICES/sample-N.wav`, strips the WAV headers to recover the raw 8-bit PCM payload, and writes it into the new SMP as `[length DWORD][raw data]`.
- Writes the corresponding byte offset into `ENGLISH-NEW.IDX`.
- `IDX[0]` is preserved as `0` (format marker slot).
- The first 4 bytes of the new SMP are the original engine header (`2E A1 08 00`), so the file is byte-compatible with the PC version of Discworld 1.

### `merge-voice-dw1-flac.py`

Reassembles a new `ENGLISH-NEW.SMP` from the original `ENGLISH.IDX` and a set of FLAC files in `VOICES/` folder.

- Reads `ENGLISH.IDX` as an array of little-endian `DWORD` offsets.
- For each non-zero entry, opens `VOICES/sample-N.flac` and writes its raw bytes into the new SMP as `[length DWORD][flac data]`. No decoding is performed — the FLAC payload is embedded as-is.
- Writes the corresponding byte offset into `ENGLISH-NEW.IDX`.
- `IDX[0]` is preserved as `0`.
- The first 4 bytes of the new SMP are replaced with the ASCII signature `FLAC` (`46 4C 41 43`, big-endian), as written by `compress_tinsel.cpp`. ScummVM checks this signature to know the sample data is compressed and
  routes it through `Audio::makeFLACStream` instead of treating it as raw PCM.

  ## A note on sample parameters

The original idea behind this fork was to re-encode the higher-quality PSX voice samples (XA-ADPCM, 44100 Hz, 16-bit) and use them with the PC version of Discworld 1 running in ScummVM, to get better-sounding speech than the native PC release (raw 8-bit, 22050 Hz).

That idea worked — the samples can be re-encoded freely. The limitation that remains is the engine itself: ScummVM reads the sample stream with the parameters baked into the game version it is running. The PC build expects
8-bit / 22050 Hz / mono; the PSX build expects 16-bit / 44100 Hz / mono. As a result, both `merge-voice-dw1-wav.py` and `merge-voice-dw1-flac.py` have to rebuild the SMP using the **same bit depth and sample rate** as the original files they replace. Putting 44100 Hz / 16-bit samples into the PC build (or 22050 Hz / 8-bit into the PSX build) does not improve the output — the engine will still play them back at its own fixed rate and bit depth.

In other words: the re-encoding pipeline succeeded; the hard ceiling is set by the Tinsel engine ScummVM implementation, not by the tools.

  ## A note on PC and PSX differences

I cross-checked extracted samples from the PC and PSX versions of the game. Most samples match one-to-one by number: sample 6000 on PC is the same line of dialogue as sample 6000 on PSX, and so on. There are, however, a few
platform-exclusive samples and one structural difference.

| Sample     | Present on PC | Present on PSX |
|------------|:-------------:|:--------------:|
| sample-108 |               | ✓              |
| sample-3264|               | ✓              |
| sample-3266|               | ✓              |
| sample-3268|               | ✓              |
| sample-3270|               | ✓              |
| sample-3545|               | ✓              |
| sample-4302|               | ✓              |
| sample-4303|               | ✓              |
| sample-4304|               | ✓              |
| sample-4305|               | ✓              |
| sample-4306|               | ✓              |
| sample-4343|               | ✓              |
| sample-5872|               | ✓              |
| sample-5884|               | ✓              |
| sample-5885|               | ✓              |
| sample-5886|               | ✓              |
| sample-5894| ✓             |                |
| sample-5895| ✓             |                |
| sample-5896| ✓             |                |
| sample-5897| ✓             |                |
| sample-5930| ✓             |                |
| sample-5966| ✓             |                |
| sample-5969| ✓             |                |
| sample-5972| ✓             |                |
| sample-5973| ✓             |                |
| sample-5978| ✓             |                |
| sample-5979| ✓             |                |
| sample-5980| ✓             |                |
| sample-6055| ✓             |                |
| sample-6091| ✓             |                |
| sample-6128| ✓             |                |
| sample-6309| ✓             |                |
| sample-6314| ✓             |                |
| sample-6518| ✓             |                |
| sample-6566| ✓             |                |
| sample-6844| ✓             |                |

Everything outside this table is identical across both versions.

### The sample-3649 split

On PC, sample-3649 is a single file. On PSX, the same recording is split across two files: sample-3648 and sample-3649. Concatenating PSX sample-3648 + sample-3649 reproduces the full audio of PC sample-3649.

### Building a PC SMP from PSX samples

To reassemble `ENGLISH.SMP` for the PC version using sound data taken from the PSX version, you need the **PC** `ENGLISH.IDX` and the **PC** sample numbering. That means:

1. **Remove** the PSX-exclusive samples (sample-108, sample-3264 and so on) so they don't occupy slots the PC build doesn't expect.
2. **Add** the PC-exclusive samples (sample-6055, sample-6091, sample-6128) — these have no PSX counterpart, so the original PC files must be kept for those slots.
3. **Merge** PSX sample-3648 + sample-3649 into a single file and rename it to sample-3649, matching the PC layout.

After these steps the samples sit at the same indices the PC build references, so game logic is preserved: the engine looks up a sample by its `ENGLISH.IDX` offset, and that offset still points to the correct line of dialogue at the correct position.