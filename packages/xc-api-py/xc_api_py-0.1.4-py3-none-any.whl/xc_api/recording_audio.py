from .schemas.recording import Recording
from pathlib import Path
from typing import Optional
from urllib.request import HTTPError, urlopen
import warnings
import miniaudio
import numpy as np
from datetime import timedelta
from yarl import URL
from functools import partial
from contextlib import contextmanager

def _fetch(url: URL) -> bytes:
    try:
      with urlopen(str(url)) as resp:
        return resp.read()

    except HTTPError as err:
      raise RuntimeError(f'Unable to fetch remote audio file: {err}')

class AudioNotLoadedError(Exception): ...

class RecordingAudio:
  _NORM = 32768.0

  def __init__(self):
    self._fetch_promise: Optional[partial[bytes]] = None
    self._original_file: Optional[Path] = None
    self._data: Optional[bytes] = None
    self._target_sr: Optional[int] = None
    self._decoded: Optional[miniaudio.DecodedSoundFile] = None
    self._name: Optional[str] = None
    self._quality: Optional[str] = None

  @property
  def sample_rate(self) -> int:
    if not self._decoded:
      raise AudioNotLoadedError()
    
    return self._decoded.sample_rate

  @contextmanager
  def load(self):
    try:
      if not self._data:
        if self._fetch_promise:
          # .from_recording(...)
          if not self._target_sr:
            raise RuntimeError()
          self._decoded = miniaudio.decode(
            data=self._fetch_promise(),
            sample_rate=self._target_sr
          )
        
        elif self._original_file:
          # .from_file(...)  
          self._decoded = miniaudio.decode_file(
            filename=str(self._original_file)
          )
        
        else:
          raise NotImplementedError()

      if not self._decoded:
        raise RuntimeError()

      yield self

    finally:
      self._decoded = None 

  @classmethod
  def from_recording(cls, recording: Recording):
    obj = cls()
    obj._fetch_promise = partial(_fetch, recording.recording_file_url)
    obj._target_sr = recording.recording_sample_rate
    obj._name = recording.recording_file_name
    if recording.recording_quality:
      obj._quality = recording.recording_quality.name
    return obj

  @classmethod
  def from_file(cls, path: Path):
    path = Path(path)
    
    if not path.exists() or not path.is_file():
      raise FileNotFoundError(path)
    
    obj = cls()
    obj._original_file = path
    obj._name = path.name
    
    return obj

  @property
  def quality(self):
    return self._quality

  def __str__(self):
    return f'RecordingAudio(name="{self._name}", quality={self._quality})'

  def save(
    self,
    directory: Path = Path.cwd(),
    name: Optional[str] = None,
  ):
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
      raise ValueError(directory)
    
    if self._data is None:
      if self._fetch_promise:
        # .from_recording(...)
        self._data = self._fetch_promise()
      
      elif self._original_file:
        # .from_file(...)
        with open(self._original_file, mode='rb') as f:
          self._data = f.read()

      else:
        raise NotImplementedError()
    
    path = directory / (name or self._name or 'recording.wav')

    with open(path, mode='wb') as f:
      f.write(self._data)

  def to_numpy(
    self, 
    start: Optional[timedelta] = None, 
    length: Optional[timedelta] = None
  ) -> np.ndarray:
    if self._decoded is None:
      raise AudioNotLoadedError()
    
    # 1. Access raw buffer
    arr = np\
      .frombuffer(self._decoded.samples, dtype=np.int16)\
      .reshape(-1, self._decoded.nchannels)
    
    # 2. Handle Slicing via Sample Rate
    sr = self.sample_rate
    start_idx = int(start.total_seconds() * sr) if start else 0
    
    if start_idx >= len(arr):
      raise ValueError("Start exceeds duration")
        
    if length:
      end_idx = start_idx + int(length.total_seconds() * sr)
      arr = arr[start_idx:end_idx]
    else:
      arr = arr[start_idx:]
    
    # 3. Cast and Normalize
    return (arr.astype(np.float32) / self._NORM).copy()

  def to_birdnet(
    self, 
    start: Optional[timedelta] = None, 
    length: Optional[timedelta] = None
  ) -> np.ndarray:
    # 1. Get sliced numpy array
    arr = self.to_numpy(start=start, length=length)

    # 2. Downmix to Mono (Averaging channels)
    if arr.ndim > 1 and arr.shape[1] > 1:
      arr = arr.mean(axis=1)
    elif arr.ndim > 1:
      arr = arr.flatten()

    # 3. BirdNET Requirement Check
    if self.sample_rate != 48000:
      warnings.warn(f"sample rate is {self.sample_rate}; BirdNET requires 48000.")

    return arr