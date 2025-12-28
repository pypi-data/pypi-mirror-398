# ailia AI Speech Python API

!! CAUTION !!
“ailia” IS NOT OPEN SOURCE SOFTWARE (OSS).
As long as user complies with the conditions stated in [License Document](https://ailia.ai/license/), user may use the Software for free of charge, but the Software is basically paid software.

## About ailia AI Speech

ailia AI Speech is a library to perform speech recognition using AI. It provides a C API for native applications, as well as a C# API well suited for Unity applications. Using ailia AI Speech, you can easily integrate AI powered speech recognition into your applications.

## Install from pip

You can install the ailia AI Speech free evaluation package with the following command.

```
pip3 install ailia_speech
```

## Install from package

You can install the ailia AI Speech from Package with the following command.

```
python3 bootstrap.py
pip3 install ./
```

## Usage

### Batch mode

In batch mode, the entire audio is transcribed at once.

```python
import ailia_speech

import librosa

import os
import urllib.request

# Load target audio
input_file_path = "demo.wav"
if not os.path.exists(input_file_path):
	urllib.request.urlretrieve(
		"https://github.com/axinc-ai/ailia-models/raw/refs/heads/master/audio_processing/whisper/demo.wav",
		"demo.wav"
	)
audio_waveform, sampling_rate = librosa.load(input_file_path, mono = True)

# Model Initialize
speech = ailia_speech.Whisper()
model_type = ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3_TURBO

# When using sensevoice
#speech = ailia_speech.SenseVoice()
#model_type = ailia_speech.AILIA_SPEECH_MODEL_TYPE_SENSEVOICE_SMALL

# Infer
speech.initialize_model(model_path = "./models/", model_type = model_type)
recognized_text = speech.transcribe(audio_waveform, sampling_rate)
for text in recognized_text:
	print(text)
```

### Step mode

In step mode, the audio is input in chunks and transcribed sequentially.

```python
import ailia_speech

import librosa

import os
import urllib.request

# Load target audio
input_file_path = "demo.wav"
if not os.path.exists(input_file_path):
	urllib.request.urlretrieve(
		"https://github.com/axinc-ai/ailia-models/raw/refs/heads/master/audio_processing/whisper/demo.wav",
		"demo.wav"
	)
audio_waveform, sampling_rate = librosa.load(input_file_path, mono = True)

# Infer
speech = ailia_speech.Whisper()
speech.initialize_model(model_path = "./models/", model_type = ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3_TURBO)
speech.set_silent_threshold(silent_threshold = 0.5, speech_sec = 1.0, no_speech_sec = 0.5)
for i in range(0, audio_waveform.shape[0], sampling_rate):
	complete = False
	if i + sampling_rate >= audio_waveform.shape[0]:
		complete = True
	recognized_text = speech.transcribe_step(audio_waveform[i:min(audio_waveform.shape[0], i + sampling_rate)], sampling_rate, complete)
	for text in recognized_text:
		print(text)
```

### Dialization mode

By specifying dialization_type, speaker diarization can be performed. When speaker diarization is enabled, speaker_id becomes valid.

```
speech.initialize_model(model_path = "./models/", model_type = ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3_TURBO, diarization_type = ailia_speech.AILIA_SPEECH_DIARIZATION_TYPE_PYANNOTE_AUDIO)
```

### Available model types

It is possible to select multiple models according to accuracy and speed. LARGE_V3_TURBO is the most recommended.

Whisper

```
ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_TINY
ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_BASE
ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_SMALL
ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_MEDIUM
ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE
ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3
ailia_speech.AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3_TURBO
```

SenseVoice

```
ailia_speech.AILIA_SPEECH_MODEL_TYPE_SENSEVOICE_SMALL
```

### Available vad versions

By default, version "4" of SileroVAD is used. The version can be specified from "4", "5", "6", and "6_2".

```
speech.initialize_model(model_path = "./models/", vad_type = AILIA_SPEECH_VAD_TYPE_SILERO, vad_version = "6_2")
```

## API specification

https://github.com/axinc-ai/ailia-sdk

