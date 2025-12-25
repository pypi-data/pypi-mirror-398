from pydantic import (
  BaseModel,
  Field,
  AnyHttpUrl,
  field_validator, model_validator,
  ConfigDict,
)
from typing import (
  Optional,
  Sequence,
  Union,
)
from ..types import *
from datetime import datetime, time, timedelta
import re
from yarl import URL

_INVALID_INPUT_STRING_VALUES = [
  '',
  '?',
  'unknown',
]

def _validate_xc_file_upload_url(value: str):
  if value.startswith('//'):
    value = f'https:{value}'
  
  invalid_values = ['', '?', 'unknown']
  if value.lower() in invalid_values:
    raise ValueError(f"Field received an invalid placeholder value: '{value}'")

  PATTERN = (
    r'^https?://xeno-canto\.org/sounds/uploaded'
    r'/(?P<user_id>[^/]+)'
    r'/(?:ffts|wave)' # "ffts"=sonogram, "wave"=oscillogram
    r'/XC(?P<recording_id>\d+)'
    r'-(?P<version>small|med|large|full)'
    r'\.(?P<file_ext>[a-z0-9]+)$'
  )

  match = re.match(PATTERN, value)
  
  if not match:
    raise ValueError(value)
  
  metadata = match.groupdict() # TODO Something with this
  
  return URL(value)

class Sonograms(BaseModel):
  model_config = ConfigDict(
    arbitrary_types_allowed=True,
  )
  
  small: URL
  medium: URL = Field(alias='med')
  large: URL
  full: URL
  
  @field_validator('small', 'medium', 'large', 'full', mode='before')
  def _validate_url_fields(cls, value, info):
    return _validate_xc_file_upload_url(value)

class Oscillograms(BaseModel):
  model_config = ConfigDict(
    arbitrary_types_allowed=True,
  )

  small: URL
  medium: URL = Field(alias='med')
  large: URL
  
  @field_validator('small', 'medium', 'large', mode='before')
  def _validate_url_fields(cls, value, info):
    return _validate_xc_file_upload_url(value)

class Recording(BaseModel):
  model_config = ConfigDict(
    # populate_by_name=True,
    # validate_by_name=True,
    arbitrary_types_allowed=True
  )

  # URL fields
  recording_page_url: URL = Field(
    alias='url',
    description='URL of the Xeno-Canto detail page.',
  )
  recording_file_url: URL = Field(
    alias='file',
    description='Direct download URL for the audio file.',
  )
  recording_license_url: URL = Field(
    alias='lic',
    description='License URL of the recording.',
  )
  
  @field_validator(
    'recording_page_url',
    'recording_file_url',
    'recording_license_url',
    mode='before',
  )
  def _validate_url_fields(cls, value, info):
    if not value.startswith('https:'):
      value = f'https:{value}'
    
    return URL(value)

  # String fields
  recording_id: str = Field(
    alias='id',
    description='Catalogue number (6-7 digit) of the recording on Xeno-Canto.',
    examples=['694038'],
  )
  animal_genus: str = Field(
    alias='gen',
    description='Generic name of the species',
    examples=['Troglodytes'],
  )
  animal_epithet: str = Field(
    alias='sp',
    description='Specific name (epithet) of the species',
    examples=['troglodytes'],
  )
  animal_common_name: str = Field(
    alias='en',
    description='English name of the species',
    examples=['Eurasian Wren'],
  )
  recording_country: str = Field(
    alias='cnt',
    description='Name of the country where the recording was made',
    examples=['Spain'],
  )
  recording_author: str = Field(
    alias='rec',
    description='Name of the recordist',
    examples=['Jacobo Ramil Millarengo'],
  )
  recording_file_name: str = Field(
    alias='file-name',
    description='Original filename of the audio file.',
    examples=['XC694038-211223_02Carrizo variaci\u00f3ns dunha frase bastante stereotipada siteD 9.30 Sisalde.mp3'],
  )

  animal_subspecies: Optional[str] = Field(
    alias='ssp',
    description='Subspecies epithet.',
    default=None,
  )
  recording_locality: Optional[str] = Field(
    alias='loc',
    description='Name of the locality where the recording was made',
    examples=['Sisalde, Ames, A Coruña, Galicia'],
    default=None,
  )
  recording_background_animals: Optional[Sequence[str]] = Field(
    description='List of background species identified in the recording.',
    alias='also',
    examples=[['Turdus viscivorus', 'Parus major']],
    default=None,
  )
  recording_remarks: Optional[str] = Field(
    alias='rmk',
    description='Additional remarks made by the recordist.',
    examples=['Male repeating a stereotyped phrase. HPF 270 Hz.'],
  )
  recording_registration_num: Optional[str] = Field(
    alias='regnr',
    description='Registration number (if specimen collected)',
  )
  recording_device: Optional[str] = Field(
    alias='dvc',
    description='Recording device used',
  )
  recording_microphone: Optional[str] = Field(
    alias='mic',
    description='Microphone used to record',
  )

  @field_validator(
    'recording_id',
    'animal_genus',
    'animal_epithet',
    'animal_subspecies',
    'animal_common_name',
    'recording_author',
    'recording_country',
    'recording_locality',
    'recording_file_name',
    'recording_background_animals',
    'recording_remarks',
    'recording_registration_num',
    'recording_device',
    'recording_microphone',
  )
  def _validate_string_fields(cls, value, info):
    if (value is None) \
    or (isinstance(value, str) and value.lower() in _INVALID_INPUT_STRING_VALUES):
      return None
    
    return value

  # Float fields
  recording_latitude: Optional[float] = Field(
    alias='lat',
    description='Latitude of the recording in decimal coordinates',
    default=None,
  )
  recording_longitude: Optional[float] = Field(
    alias='lon',
    description='Longitude of the recording in decimal coordinates',
    default=None,
  )
  recording_altitude: Optional[float] = Field(
    alias='alt',
    description='Altitude of the recording location in meters',
    default=None,
  )
  recording_temp: Optional[float] = Field(
    alias='temp',
    description='Temperature during recording (if applicable).',
  )
  recording_sample_rate: int = Field(
    alias='smp',
    description='Sample rate of the recording',
  )
  @field_validator(
    'recording_latitude',
    'recording_longitude',
    'recording_altitude',
    'recording_temp',
    mode='before'
  )
  def _validate_float_fields(cls, value, info):
    try:
      return float(value)
    except:
      return None

  # Date fields
  recording_date: Optional[date] = Field(
    alias='date',
    description='Date the recording was made',
    examples=['2021-12-23'],
  )
  recording_upload_date: Optional[date] = Field(
    alias='uploaded',
    description='Date the recording was uploaded',
    examples=['2021-12-27'],
  )
  @field_validator(
    'recording_date',
    'recording_upload_date',
    mode='before'
  )
  def _validate_date_fields(cls, value, info):
    if isinstance(value, str) and value.lower() in _INVALID_INPUT_STRING_VALUES:
      return None
    
    try:
      return datetime.fromisoformat(value)
    
    except:
      return None

  # Time fields
  recording_time: Optional[time] = Field(
    alias='time',
    description='Time of day when the recording was made',
    examples=['09:30'],
  )
  @field_validator('recording_time', mode='before')
  def _validate_time_fields(cls, value, info):
    if not isinstance(value, str) or value.lower() in _INVALID_INPUT_STRING_VALUES:
      return None
    
    try:
      # 1. Try standard ISO format first (fastest)
      return time.fromisoformat(value)
    except ValueError:
      try:
        # 2. Handle '6:05' or '18:5' style by parsing specifically
        # %H handles single digits like '6' as '06' automatically
        if len(value.split(':')) == 2:
          return datetime.strptime(value, "%H:%M").time()
        elif len(value.split(':')) == 3:
          return datetime.strptime(value, "%H:%M:%S").time()
      except ValueError:
        return None
    return None

  # Duration fields
  recording_length: Optional[timedelta] = Field(
    alias='length',
    description='Length of the recording in minutes and seconds.',
    examples=['4:08'],
  )
  @field_validator('recording_length', mode='before')
  def _validate_timedelta_fields(cls, value, info):
    try:
      t = datetime.strptime(value, '%M:%S')
      return timedelta(minutes=t.minute, seconds=t.second)
    except:
      return None

  # Boolean fields
  recording_animal_sighted: Optional[bool] = Field(
    alias='animal-seen',
    description='Whether the recorded animal was seen.',
  )
  recording_playback_used: Optional[bool] = Field(
    alias='playback-used',
    description='Whether playback was used to lure the animal.',
  )
  recording_is_automatic: Optional[bool] = Field(
    alias='auto',
    description='Indicator for automatic/non-supervised recording',
  )

  @field_validator(
    'recording_animal_sighted',
    'recording_playback_used',
    'recording_is_automatic',
    mode='before'
  )
  def _validate_boolean_fields(cls, value, info):
    if isinstance(value, bool):
      return value
    
    elif isinstance(value, str):
      if value.lower().startswith('yes'):
        return True
      elif value.lower().startswith('no'):
        return False
    
    return None

  # Typed fields
  animal_group: Optional[AnimalGroup] = Field(
    alias='grp',
    description='Group to which the species belongs (birds, grasshoppers, bats)',
    default=None,
  )
  recording_sound_type: Optional[AnimalSoundType] = Field(
    alias='type',
    description='Sound type of the recording',
    default=None,
  )
  animal_sex: Optional[AnimalSex] = Field(
    title='Sex of the recorded animal',
    alias='sex',
    
  )
  animal_life_stage: Optional[Union[AnimalLifeStage, Sequence[AnimalLifeStage]]] = Field(
    title='Life stage of the recorded animal',
    alias='stage',
  )
  recording_method: Optional[RecordingMethod] = Field(
    alias='method',
    description='Recording method used',
    default=None,
  )
  recording_quality: Optional[RecordingQuality] = Field(
    alias='q',
    description='Quality rating of the recording.',
  )

  @field_validator('animal_group', mode='before')
  def _validate_animal_group_field(cls, value, info):
    return value if value in AnimalGroup.__args__ else None
  
  @field_validator('recording_sound_type', mode='before')
  def _validate_recording_sound_type(cls, value, info):
    return value if value in AnimalSoundType.__args__ else None

  @field_validator('animal_sex', mode='before')
  def _validate_animal_sex_field(cls, value, info):
    return value if value in AnimalSex.__args__ else None

  @field_validator('animal_life_stage', mode='before')
  def _validate_animal_life_stage_field(cls, value, info):
    return value if value in AnimalLifeStage.__args__ else None

  @field_validator('recording_method', mode='before')
  def _validate_recording_method_field(cls, value, info):
    return value if value in RecordingMethod.__args__ else None

  @field_validator('recording_quality', mode='before')
  def _validate_recording_quality_field(cls, value, info):
    try:
      return RecordingQuality[value.capitalize()]
    except:
      return None


  # Nested model fields
  recording_sonograms: Sonograms = Field(
    alias='sono',
    description='An object with the URLs to the four versions of sonograms.',
  )
  recording_oscillograms: Oscillograms = Field(
    alias='osci',
    description='An object with the URLs to the three versions of oscillograms.',
  )