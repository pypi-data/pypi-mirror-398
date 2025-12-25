# Xeno Canto API Client for Python

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org)
[![Pydantic](https://img.shields.io/badge/data-Pydantic-red)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intuitive, type-safe Python wrapper for the [Xeno-Canto API](https://xeno-canto.org/explore/api).  
Streamline your bioacoustics and machine learning workflows by searching, filtering, and processing wildlife recordings with full validation and IDE autocompletion.  

## Project Sponsors
<table>
  <tr>
    <td><img src="https://raw.githubusercontent.com/yuvalrot479/xc-api-py/main/.github/asp-lab-logo.jpg" alt="asp-lab-logo"></td>
    <td><img src="https://raw.githubusercontent.com/yuvalrot479/xc-api-py/main/.github/tel-hai-logo.png" alt="tel-hai-logo"></td>
  </tr>
</table>

## Disclaimer
This project is a free and open-source tool intended for educational purposes only;  
This project is provided AS IS without any warranty - use at your own risk;  
This project is not associated with, maintained by, or endorsed by the [Xeno-Canto Foundation](https://xeno-canto.org/);  
Users are responsible for adhering to the [Xeno-Canto Terms of Use](https://xeno-canto.org/about/terms) and respecting the licensing of individual recordings.  

## Quickstart

```bash
pip install xc-api-py
```
```bash
pdm add xc-api-py
```

## Basic Usage
```py
from xc_api import Client, SearchQuery, tags
from datetime import timedelta

# Instanciate a client with your Xeno Canto API key
client = Client('Your API key')

# Create a query
query = SearchQuery(
  animal_genus='acrocephalus',
  animal_sex='male',
  recording_length=tags.Length.at_least(timedelta(seconds=10)),
  recording_country=tags.Country('germany'),
)

# Search the API, optionally pass a limit argument
recordings = client.find(query, limit=10)

# Get a specific recording
recording = client.get_by_id('129150')
```

## Advanced Usage
### Pandas
```py
from xc_api import SearchQuery, RecordingAudio
import pandas as pd

query = SearchQuery(...)
recordings = client.find(query)
df = pd.DataFrame.from_records([r.model_dump() for r in recordings])
```

### SoundDevice
```py
from xc_api import SearchQuery, RecordingAudio
import sounddevice as sd

recording = client.get_by_id(...)

audio = RecordingAudio.from_recording(recording)

with audio.load() as a:
  sd.play(a.to_numpy(), a.sample_rate)
  sd.wait()

# Optional: save original file locally
audio.save()
```

### BirdNET
```py
from xc_api import SearchQuery, RecordingAudio
from birdnetlib import RecordingBuffer
from birdnetlib.analyzer import Analyzer
from datetime import timedelta

analyzer = Analyzer()

query = SearchQuery(
  animal_group='birds',
  recording_sample_rate=tags.SampleRate(48000), # IMPORTANT: BirdNET analyzer expects 48000Khz
)

recording = client.find_one(query, limit=1)

audio = RecordingAudio.from_recording(recording)

with audio.load() as a:
  arr = a.to_birdnet(length=timedelta(seconds=3.0)) # Optional: Segment the audio

buffer = RecordingBuffer(analyzer, arr)
buffer.analyze()

for detection in buffer.detections:
  ...
```