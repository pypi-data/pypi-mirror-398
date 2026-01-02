from pydantic import (
  BaseModel,
  Field,
  field_validator,
  ConfigDict,
  BeforeValidator,
)
from typing import (
  Optional,
  Sequence,
  Union,
  Annotated,
)
from ..types import *
from datetime import time, timedelta
import yarl

from .field_validators import *

Float = Annotated[Optional[float], BeforeValidator(validate_float)]
Date = Annotated[Optional[date], BeforeValidator(validate_date)]
Time = Annotated[Optional[time], BeforeValidator(validate_time)]
URL = Annotated[Optional[yarl.URL], BeforeValidator(validate_url)]
String = Annotated[Optional[str], BeforeValidator(validate_string)]
Boolean = Annotated[Optional[bool], BeforeValidator(validate_boolean)]
Timedelta = Annotated[Optional[timedelta], BeforeValidator(validate_timedelta)]
XCUploadURL = Annotated[Optional[yarl.URL], BeforeValidator(validate_xc_file_upload_url)]
XCQuality = Annotated[Optional[QualityRating], BeforeValidator(validate_xc_recording_quality)]

class LeanRecording(BaseModel):
  model_config = ConfigDict(
    arbitrary_types_allowed=True
  )

  # Animal fields
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
  animal_subspecies: String = Field(
    alias='ssp',
    description='Subspecies epithet.',
    default=None,
  )

  # Recording fields
  recording_id: str = Field(
    alias='id',
    description='Catalogue number (6-7 digit) of the recording on Xeno-Canto.',
    examples=['694038'],
  )
  recording_file_url: Optional[URL] = Field(
    alias='file',
    description='Direct download URL for the audio file.',
    default=None,
  )
  recording_license_url: URL = Field(
    alias='lic',
    description='License URL of the recording.',
  )
  recording_file_name: str = Field(
    alias='file-name',
    description='Original filename of the audio file.',
    examples=['XC694038-211223_02Carrizo variaci\u00f3ns dunha frase bastante stereotipada siteD 9.30 Sisalde.mp3'],
  )
  recording_latitude: Optional[Float] = Field(
    alias='lat',
    description='Latitude of the recording in decimal coordinates',
    default=None,
  )
  recording_longitude: Optional[Float] = Field(
    alias='lon',
    description='Longitude of the recording in decimal coordinates',
    default=None,
  )
  recording_quality: Optional[XCQuality] = Field(
    alias='q',
    description='''
    Recordings are rated by quality.
    Quality ratings range from A (highest quality) to E (lowest quality).
    To search for recordings that match a certain quality rating, use the q tag.
    This field also accepts '<' and '>' operators. For example:

    q:A will return recordings with a quality rating of A.
    q:"<C" will return recordings with a quality rating of D or E.
    q:">C" will return recordings with a quality rating of B or A.
    
    Note that not all recordings are rated. Unrated recordings will not be returned for a search on quality rating.
    ''',
    default=None,
  )


class Sonograms(BaseModel):
  model_config = ConfigDict(
    arbitrary_types_allowed=True,
  )
  
  small: XCUploadURL
  medium: XCUploadURL = Field(alias='med')
  large: XCUploadURL
  full: XCUploadURL

class Oscillograms(BaseModel):
  model_config = ConfigDict(
    arbitrary_types_allowed=True,
  )

  small: XCUploadURL
  medium: XCUploadURL = Field(alias='med')
  large: XCUploadURL

class Recording(LeanRecording):
  model_config = ConfigDict(
    # populate_by_name=True,
    # validate_by_name=True,
    arbitrary_types_allowed=True
  )

  # Animal fields
  animal_common_name: str = Field(
    alias='en',
    description='English name of the species',
    examples=['Eurasian Wren'],
  )
  animal_sex: Optional[AnimalSex] = Field(
    title='Sex of the recorded animal',
    alias='sex',
    
  )
  @field_validator('animal_sex', mode='before')
  def validate_animal_sex(cls, v):
    return v if v in AnimalSex.__args__ else None
  animal_life_stage: Optional[Union[AnimalLifeStage, Sequence[AnimalLifeStage]]] = Field(
    title='Life stage of the recorded animal',
    alias='stage',
  )
  @field_validator('animal_life_stage', mode='before')
  def validate_animal_life_stage(cls, v):
    return v if v in AnimalLifeStage.__args__ else None
  animal_group: Optional[AnimalGroup] = Field(
    alias='grp',
    description='Group to which the species belongs (birds, grasshoppers, bats)',
    default=None,
  )
  @field_validator('animal_group', mode='before')
  def validate_animal_group(cls, v):
    return v if v in AnimalGroup.__args__ else None
  
  # Recording fields
  recording_sonograms: Sonograms = Field(
    alias='sono',
    description='An object with the URLs to the four versions of sonograms.',
  )
  recording_oscillograms: Oscillograms = Field(
    alias='osci',
    description='An object with the URLs to the three versions of oscillograms.',
  )
  recording_page_url: URL = Field(
    alias='url',
    description='URL of the Xeno-Canto detail page.',
  )
  recording_country: String = Field(
    alias='cnt',
    description='Name of the country where the recording was made',
    examples=['Spain'],
  )
  recording_author: String = Field(
    alias='rec',
    description='Name of the recordist',
    examples=['Jacobo Ramil Millarengo'],
  )
  recording_locality: String = Field(
    alias='loc',
    description='Name of the locality where the recording was made',
    examples=['Sisalde, Ames, A Coruña, Galicia'],
    # default=None,
  )
  recording_background_animals: Optional[Sequence[str]] = Field(
    description='List of background species identified in the recording.',
    alias='also',
    examples=[['Turdus viscivorus', 'Parus major']],
    default=None,
  )
  recording_remarks: String = Field(
    alias='rmk',
    description='Additional remarks made by the recordist.',
    examples=['Male repeating a stereotyped phrase. HPF 270 Hz.'],
  )
  recording_registration_num: String = Field(
    alias='regnr',
    description='Registration number (if specimen collected)',
  )
  recording_device: String = Field(
    alias='dvc',
    description='Recording device used',
  )
  recording_microphone: String = Field(
    alias='mic',
    description='Microphone used to record',
  )
  recording_altitude: Optional[Float] = Field(
    alias='alt',
    description='Altitude of the recording location in meters',
    default=None,
  )
  recording_temp: Float = Field(
    alias='temp',
    description='Temperature during recording (if applicable).',
  )
  recording_sample_rate: int = Field(
    alias='smp',
    description='Sample rate of the recording',
  )
  recording_date: Date = Field(
    alias='date',
    description='Date the recording was made',
    examples=['2021-12-23'],
  )
  recording_upload_date: Date = Field(
    alias='uploaded',
    description='Date the recording was uploaded',
    examples=['2021-12-27'],
  )
  recording_time: Time = Field(
    alias='time',
    description='Time of day when the recording was made',
    examples=['09:30'],
  )
  recording_length: Timedelta = Field(
    alias='length',
    description='Length of the recording in minutes and seconds.',
    examples=['4:08'],
  )
  recording_animal_sighted: Boolean = Field(
    alias='animal-seen',
    description='Whether the recorded animal was seen.',
  )
  recording_playback_used: Boolean = Field(
    alias='playback-used',
    description='Whether playback was used to lure the animal.',
  )
  recording_is_automatic: Boolean = Field(
    alias='auto',
    description='Indicator for automatic/non-supervised recording',
  )
  recording_sound_type: Optional[AnimalSoundType] = Field(
    alias='type',
    description='Sound type of the recording',
    default=None,
  )
  @field_validator('recording_sound_type', mode='before')
  def validate_recording_sound_type(cls, v):
    return v if v in AnimalSoundType.__args__ else None
  recording_method: Optional[RecordingMethod] = Field(
    alias='method',
    description='Recording method used',
    default=None,
  )
  @field_validator('recording_method', mode='before')
  def validate_recording_method(cls, v):
    return v if v in RecordingMethod.__args__ else None
