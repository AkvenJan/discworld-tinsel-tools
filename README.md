# Discworld Tools
Scripts and utilities for Discworld games based on Tinsel engine

Forked from https://github.com/adventurebrew/kolminey

I took those sources and modified them to support PSX version of Discworld 1 game

## Audio formats

| Version        | Format                          | Sample rate | Channels | Decodes to               |
|----------------|---------------------------------|-------------|----------|--------------------------|
| Discworld 1 PC | Raw 8-bit unsigned PCM          | 22050 Hz    | mono     | 8-bit 22050 Hz WAV       |
| Discworld 1 PSX| XA-ADPCM 4-bit (Sony SPU)       | 44100 Hz    | mono     | 16-bit 44100 Hz WAV      |
| Discworld 2 PC | Tinsel ADPCM 6-bit (custom)     | 22050 Hz    | mono     | 16-bit 22050 Hz WAV      |

The PSX version stores voice samples as Sony XA-ADPCM inside `ENGLISH.SMP`, indexed by `ENGLISH.IDX`. The PC version stores the same samples as raw 8-bit unsigned PCM. Both can be unpacked to standard WAV files.

## Scripts

### `split-text.py`

Parses `english.txt` — the game's text resource for both PC and PSX versions — into a plain-text file with one line per speech line, prefixed by the actor/speaker number. Format of the file is identical for both PC and PSX. There is a template in `/research` folder for 010 Editor with description of file structure:

```
0 "So what happened?"
0 "Nothing! Nothing happened!
That's just the point."
1 "Steal? Now do I look like a thief?"
1 "My stick! They all want my magic stick!"
```

The speaker index corresponds to the voice sample referenced by the same line in the script data, so the output can be matched against the extracted `.wav` files. I didn't research the accurate correlation. Maybe later

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

### `merge-text.py`

Reassembles a new `ENGLISH-NEW.TXT` from the `DIALOGUE/` folder produced by `split-text.py` 

- Opens `DIALOGUE\ENGLISH-PARTxxxx.TXT` and merge them following the format

I didn't the split - merge functional of these two scripts

### `merge-voice-dw1-wav.py`

Reassembles a new `ENGLISH-NEW.SMP` from the original `ENGLISH.IDX` and a set of WAV files in `VOICES/` folder.
WAV files need to be 8-bit 22050 Hz mono. There is no check on this, the game in ScummVM will just have grinding sound.

- Reads `ENGLISH.IDX` as an array of little-endian `DWORD` offsets.
- For each non-zero entry, opens `VOICES/sample-N.wav`, strips the WAV headers to recover the raw 8-bit PCM payload, and writes it into the new SMP as `[length DWORD][raw data]`.
- Writes the corresponding byte offset into `ENGLISH-NEW.IDX`.
- `IDX[0]` is preserved as `0` (format marker slot).
- The first 4 bytes of the new SMP are the original engine header (`2E A1 08 00`), so the file is byte-compatible with the PC version of Discworld 1.

### `merge-voice-dw1-compressed.py`

Reassembles a new `ENGLISH-NEW.SMP` from the original `ENGLISH.IDX` and a set of compressed audio samples in `VOICES/` folder.
Usage:
    python merge-voice.py --flac
    python merge-voice.py --mp3
    python merge-voice.py --ogg

- Reads `ENGLISH.IDX` as an array of little-endian `DWORD` offsets.
- For each non-zero entry, opens `VOICES/sample-N.flac`, `VOICES/sample-N.mp3` or `VOICES/sample-N.ogg` and writes its raw bytes into the new SMP as `[length DWORD][flac data]`. No decoding is performed — the audio payload is embedded as-is.
- Writes the corresponding byte offset into `ENGLISH-NEW.IDX`.
- `IDX[0]` (first 4 bytes of the new IDX) replaced with the ASCII signature `FLAC`, `MP3 ` or `OGG `.
- The first 4 bytes of the new SMP are replaced with the ASCII signature `FLAC`, `MP3 ` or `OGG `. ScummVM checks this signature to know the sample data is compressed and routes it through `Audio::makeFLACStream` for FLAC (`Audio::makeMP3Stream` for MP3 or `Audio::makeVorbisStream` for OGG) instead of treating it as raw PCM.

  ## A note on sample parameters

The original idea behind this fork was to extract the higher-quality PSX voice samples (XA-ADPCM, 44100 Hz, 16-bit) and use them with the PC version of Discworld 1 running in ScummVM, to get better-sounding speech than the native PC release (raw 8-bit, 22050 Hz).

The solution is fully working. There is a particular behaviour in how the ScummVM engine handles Discworld 1 on PC:

- **When SMP uses raw PCM**, the samples are stored inside SMP as raw data without any header. ScummVM sees that the SMP/IDX headers carry no compression flag and treats the data as native Raw 8-bit 22050 Hz mono unsigned PCM. For Discworld 1 on PC these parameters are hardcoded into the engine, so any PCM inside SMP will be played back as 8-bit 22050 Hz regardless of the actual content. Game will run nativily or in ScummVM engine

- **When SMP and IDX carry a compression flag** (FLAC, OGG or MP3 header), the samples are stored inside SMP with their own individual headers. In this case ScummVM passes each sample to the matching decoder, which processes every sample individually according to the parameters embedded in the sample itself. In this case 16-bit 44100 Hz will play back as 16-bit 44100 Hz. Game will only run in ScummVM


That idea worked — the samples can be re-encoded freely. The limitation that remains is the format:

- `merge-voice-dw1-wav.py` have to rebuild the SMP using the **same bit depth and sample rate** as the original files they replace (PSX 16-bit / 44100 Hz / mono needed to be downconverted to 8-bit / 22050 Hz / mono before merging)

- `merge-voice-dw1-flac.py` merge compressed Flac samples with **any bit depth and sample rate**

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

Everything outside this table is identical across both versions. Samples themselves can be different (slightly different audio or manner of speech, but they are inline with `ENGLISH.TXT`).

### The sample-3649 split

On PC, sample-3649 is a single file. On PSX, the same recording is split across two files: sample-3648 and sample-3649. Concatenating PSX sample-3648 + sample-3649 reproduces the full audio of PC sample-3649.

### Building a PC SMP from PSX samples

To reassemble `ENGLISH.SMP` for the PC version using sound data taken from the PSX version, you need the **PC** `ENGLISH.IDX` and the **PC** sample numbering. That means:

0. **Unpack** PC `ENGLISH.SMP` into different folder, cross-check PC and PSX samples.
1. **Remove** the PSX-exclusive samples (sample-108, sample-3264 and so on) so they don't occupy slots the PC build doesn't expect.
2. **Add** the PC-exclusive samples (sample-6055, sample-6091, sample-6128) — these have no PSX counterpart, so the original PC files must be kept for those slots.
3. **Merge** PSX sample-3648 + sample-3649 into a single file and rename it to sample-3649, matching the PC layout.

After these steps the samples sit at the same indices the PC build references, so game logic is preserved: the engine looks up a sample by its `ENGLISH.IDX` offset, and that offset still points to the correct line of dialogue at the correct position.

After the sample set is prepared, all resulting WAV files must be mass-converted to FLAC/MP3.OGG. On Windows this can be done with PowerShell using ffmpeg. For example for FLAC:

```powershell
Get-ChildItem *.wav | ForEach-Object {
    .\ffmpeg.exe -i $_.FullName -map_metadata -1 ($_.BaseName + ".flac")
}
```

The resulting compressed files must be placed in the `VOICES/` folder. Now put `VOICES/` folder and original PC `ENGLISH.IDX` near the script `merge-voice-dw1-compressed.py` and run it.