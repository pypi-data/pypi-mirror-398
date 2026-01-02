from pydantic import (
  BaseModel,
  Field,
  field_serializer,
  field_validator,
)
from typing import (
  Optional,
  Sequence,
)
from datetime import (
  datetime,
  timedelta,
  timezone,
)
import re

from ..types import *
from ..search_tags import *
from .. import search_tags
from .. import utils

class SearchQuery(BaseModel):
  # NOTE https://xeno-canto.org/help/search#advanced

  # String fields
  animal_genus: Optional[str] = Field(
    serialization_alias='gen',
    description="Genus is part of a species' scientific name, so it is searched by default when performing a basic search (as mentioned above).\
      But you can use the gen tag to limit your search query only to the genus field.\
        So gen:zonotrichia will find all recordings of sparrows in the genus Zonotrichia.\
          Similarly, ssp can be used to search for subspecies.\
            These fields use a 'starts with' rather than 'contains' query and accept a 'matches' operator.",
    default=None,
  )
  animal_epithet: Optional[str] = Field(
    serialization_alias='sp',
    default=None,
  )
  recording_author: Optional[str] = Field(
    serialization_alias='rec',
    title='Recordist',
    description="To search for all recordings from a particular recordist, use the rec tag. (...).\
      This field accepts a 'matches' operator.",
    examples=[
      {'John': 'will return all recordings from recordists whose names contain the string "John".'}
    ],
    default=None,
  )
  recording_location: Optional[str] = Field(
    serialization_alias='loc',
    title='Location',
    description="To return all recordings from a specific location, use the loc tag.\
      For example loc:tambopata.\
        This field uses a 'any of the individual words in the text starts with' query,\
          requires at least three characters and accepts a 'matches' operator.",
    default=None,
  )
  recording_remarks: Optional[str] = Field(
    serialization_alias='rmk',
    title='Recordist remarks',
    description="Many recordists leave remarks about the recording and this field can be searched using the rmk tag, e.g. rmk:flock.\
      The remarks field contains free text, so it is unlikely to produce complete results.\
        Note that information about whether the recorded animal was seen or if playback was used, formerly stored in remarks,\
          now can be searched using dedicated fields! This field searches for individuals words in the text starting with the term(s);\
            it also accepts a 'matches' operator.",
    default=None,
  )
  recording_id: Optional[RecordingId] = Field(
    serialization_alias='nr',
    title='XC number',
    description="All recordings on xeno-canto are assigned a unique catalog number (generally displayed in the form XC76967).\
      To search for a known recording number, use the nr tag: for example nr:76967.\
        You can also search for a range of numbers as nr:88888-88890.",
    default=None,
  )
  recording_license: Optional[str] = Field(
    serialization_alias='lic',
    title='Recording license',
    description="Recordings on xeno-canto are licensed under a small number of different Creative Commons licenses.\
      You can search for recordings that match specific license conditions using the lic tag.\
        License conditions are Attribution (BY), NonCommercial (NC), ShareAlike (SA), NoDerivatives (ND) and Public Domain/copyright free (CC0).\
          Conditions should be separated by a '-' character.\
            For instance, to find recordings that are licensed under an Attribution-NonCommercial-ShareAlike license, use lic:BY-NC-SA;\
              for \"no rights reserved\" recordings, use lic:PD.\
                See the Creative Commons website for more details about the individual licenses.",
    default=None,
  )
  animal_registration_num: Optional[str] = Field(
    serialization_alias='regnr',
    title='Registration number of specimen (when collected)',
    description='''
      The regnr tag can be used to search for animals that were sound
       recorded before ending up in a (museum) collection.
      This tag also accepts a 'matches' operator.
    ''',
    default=None,
  )
  recording_device: Optional[str] = Field(
    serialization_alias='dvc',
    description='''
      Use the dvc (device) and mic (microphone) tags to search for specific recording equipment.
    ''',
    default=None,
  )
  recording_microphone: Optional[str] = Field(
    title='Microphone',
    serialization_alias='mic',
    default=None,
  )
  recording_sound_type: Optional[AnimalSoundType] = Field(
    serialization_alias='type',
    title='The sound type of the recording',
    description='''
      To search for recordings of a particular sound type, use the type tag.
      For instance, type:song will return all recordings identified as songs.
      Note that options may pertain to a specific group only, e.g. 'searching song' is a search term used for grasshoppers, but not for birds.
      Valid values for this tag are: (...). This tag always uses a 'matches' operator.
      Up until 2022, the 'type' tag used to search a free text field.
      We have retained the option to search for non-standardized sound types by using the othertype tag.
      This tag also accepts a 'matches' operator, e.g. othertype:"=wing flapping".
    ''',
    default=None,
  )
  animal_group: Optional[AnimalGroup] = Field(
    serialization_alias='grp',
    description="Use the grp tag to narrow down your search to a specific group.\
      This tag is particularly useful in combination with one of the other tags. Valid group values are (...).\
        You can also use their respective ids (1 to 5), so grp:2 will restrict your search to grasshoppers.\
          Soundscapes are a special case, as these recordings may include multiple groups.\
            Use grp:soundscape or grp:0 to search these.",
    examples=[
      'birds',
      'grasshoppers',
      'bats',
      'frogs',
      'land mammals'
    ],
    default=None,
  )
  animal_sex: Optional[AnimalSex] = Field(
    serialization_alias='sex',
    title='Sex',
    description="Formerly included under 'sound types', the sex tag can now be used independently.\
      Valid values for this tag are: (...).\
        This tag always uses a 'matches' operator.",
    default=None,
  )
  recording_area: Optional[RecordingArea] = Field(
    serialization_alias='area',
    title='World area',
    examples=[
      'africa',
      'america',
      'asia',
      'australia',
      'europe',
    ],
    default=None,
  )
  animal_life_stage: Optional[AnimalLifeStage] = Field(
    serialization_alias='stage',
    title='Life stage',
    description="Values of the stage tag were previously included under 'sound types' as well.\
      Valid values are: (...).\
        This tag always uses a 'matches' operator.",
    default=None,
  )
  
  @field_validator(
    'recording_id'
  )
  def _validate_recording_id(cls, v: Union[RecordingId, str, int]):
    
    if isinstance(v, RecordingId):
      return f'{v.a}-{v.b}'

    else:
      s = str(v).strip()
      PATTERN = r'^(?i:xc)?(?P<recording_id>\d{1,9})$'
      match = re.match(PATTERN, s)
      if not match:
        raise ValueError(v)
      
      return RecordingId(int(match.group('recording_id')))
  
  @field_serializer(
    'animal_genus',
    'animal_epithet',
    'recording_author',
    'recording_location',
    'recording_remarks',
    'recording_license',
    'animal_registration_num',
    'recording_device',
    'recording_microphone',
    'recording_sound_type',
    'animal_group',
  )
  def _serialize_text_fields(self, v: Optional[str]):
    if v is None:
      return None
    return utils.wrap_text(v)

  # Sequenced fields
  recording_background_animals: Optional[Sequence[str]] = Field(
    serialization_alias='also',
    title='Background species',
    description="To search for recordings that have a given species in the background, use the also tag.\
      Use this field to search for both species (common names in English and scientific names)\
        and families (scientific names).",
    examples=[
      {'formicariidae': 'will return all recordings that have a member of the Antthrush family identified as a background voice.'},
    ],
    default=None,
  )

  @field_serializer('recording_background_animals')
  def _serialize_sequenced_text_fields(self, value: Optional[Sequence[str]], info):
    if value is None:
      return None
    return ','.join(utils.wrap_text(s) for s in value)

  # Integer fields
  recording_year: Optional[int] = Field(
    serialization_alias='year',
    default=None,
  )
  recording_month: Optional[int] = Field(
    serialization_alias='month',
    default=None,
  )
  collection_year: Optional[int] = Field(
    serialization_alias='colyear',
    description='''
      The year and month tags allow you to search for recordings that were recorded on a certain date.
      The following query will find all recordings that were recorded in May of 2010: year:2010 month:5. Similarly,
       month:6 will find recordings that were recorded during the month of June in any year.
      Both tags also accept '>' (after) and '<' (before).
    ''',
    default=None,
  )
  collection_month: Optional[int] = Field(
    serialization_alias='colmonth',
    description='''
      The year and month tags allow you to search for recordings that were recorded on a certain date.
      The following query will find all recordings that were recorded in May of 2010: year:2010 month:5. Similarly,
       month:6 will find recordings that were recorded during the month of June in any year.
      Both tags also accept '>' (after) and '<' (before).
    ''',
    default=None,
  )

  @field_validator(
    'recording_year',
    'collection_year',
  )
  def _validate_year_fields(cls, value: int, info):
    today = datetime.now(timezone.utc)
    if value < 1970 or value > today.year:
      raise ValueError(value)
    return value

  @field_validator(
    'recording_month',
    'collection_month',
  )
  def _validate_month_fields(cls, value: int, info):
    if value < 1 or value > 12:
      raise ValueError(value)
    return value

  # Boolean fields
  recording_animal_seen: Optional[bool] = Field(
    serialization_alias='seen',
    title='Animal seen',
    description="Two tags (seen and playback respectively) that previously were stored as part of Recordist remarks, but now can be used independently.\
      Both only accept yes and no as input.\
        For example, use seen:yes playback:no to search for recordings where the animal was seen,\
          but not lured by playback.",
    default=None,
  )
  recording_playback_used: Optional[bool] = Field(
    serialization_alias='playback',
    title='Was playback used to lure the animal?',
    description='''
      Two tags (seen and playback respectively) that previously were stored as part of Recordist remarks,
       but now can be used independently. Both only accept yes and no as input.
      For example, use seen:yes playback:no to search for recordings where the animal was seen,
       but not lured by playback.
    ''',
    default=None,
  )
  recording_automatic: Optional[bool] = Field(
    serialization_alias='auto',
    description='''
      The auto tag searches for automatic (non-supervised) recordings.
      This tag accepts yes and no.
    ''',
    default=None,
  )
  
  @field_serializer(
    'recording_animal_seen',
    'recording_playback_used',
    'recording_automatic',
  )
  def _serialize_boolean_fields(self, value: Optional[bool]):
    if value is None:
      return None
    elif value is True:
      return 'yes'
    elif value is False:
      return 'no'
    raise ValueError(value)

  # Search tag fields
  recording_latitude: Optional[Latitude] = Field(
    serialization_alias='lat',
    title='Latitude',
    description='''
      The latitude of the recording in decimal coordinates.
      There are two sets of tags that can be used to search via geographic coordinates.
      The first set of tags is lat and lon.
      These tags can be used to search within one degree in either direction of the given coordinate,
       for instance: lat:-12.234 lon:-69.98.
      This field also accepts '<' and '>' operators;
       e.g. use lat:">66.5" to search for all recordings made above the Arctic Circle.
    ''',
    default=None,
  )
  recording_longitude: Optional[Longitude] = Field(
    serialization_alias='lon',
    title='Longitude',
    description='''
      The longitude of the recording in decimal coordinates.
      The latitude of the recording in decimal coordinates.
      There are two sets of tags that can be used to search via geographic coordinates.
      The first set of tags is lat and lon.
      These tags can be used to search within one degree in either direction of the given coordinate,
       for instance: lat:-12.234 lon:-69.98.
      This field also accepts '<' and '>' operators;
       e.g. use lat:">66.5" to search for all recordings made above the Arctic Circle.
    ''',
    default=None,
  )
  recording_since: Optional[Since] = Field(
    serialization_alias='since',
    description='''
      The since tag allows you to search for recordings that have been uploaded since a certain date.
      Using a simple integer value such as since:3 will find all recordings uploaded in the past 3 days.
      If you use a date with a format of YYYY-MM-DD, it will find all recordings uploaded since that date (e.g. since:2012-11-09).
      Note that this search considers the upload date, not the date that the recording was made.',
    ''',
    default=None,
  )
  recording_quality: Optional[RecordingQuality] = Field(
    serialization_alias='q',
    title='Recording quality',
    description="Recordings are rated by quality.\
      Quality ratings range from A (highest quality) to E (lowest quality).\
        To search for recordings that match a certain quality rating, use the q tag.\
          This field also accepts '<' and '>' operators.",
    examples=[
      {'A':    'will return recordings with a quality rating of A.'},
      {'"<C"': 'will return recordings with a quality rating of D or E.'},
      {'">C"': 'will return recordings with a quality rating of B or A.'}
    ],
    default=None,
  )
  recording_length: Optional[Length] = Field(
    serialization_alias='len',
    title='Recording length',
    description='''
      To search for recordings that match a certain length (in seconds), use the len tag.
      This field also accepts '<' , '>' and '=' operators.
    ''',
    examples=[
      {'10':       'will return recordings with a duration of 10 seconds (with a margin of 1%, so actually between 9.9 and 10.1 seconds'},
      {'10-15':    'will return recordings lasting between 10 and 15 seconds.'},
      {'"<30"':    'will return recordings half a minute or shorter in length.'},
      {'">120"':   'will return recordings longer than two minutes in length.'},
      {'"=19.8"':  'will return recordings lasting exactly 19.8 seconds, dropping the default 1% margin.'},
    ],
    default=None,
  )
  recording_temp: Optional[Temp] = Field(
    serialization_alias='temp',
    title='Temperature during recording (applicable to specific groups only)',
    description='''
      The temp tag for temperature currently also applies only to grasshoppers.
      This field also accepts '<' and '>' operators.
      Use temp:25 to search for sounds recorded between 25-26 °C or temp:">20" for temperatures over 20 °C.
    ''',
    default=None,
  )

  recording_method: Optional[RecordingMethod] = Field(
    serialization_alias='method',
    title='Recording method',
    description="The method tag accepts the following, group-dependent values: (...).\
      Do not forget to enclose the term between double quotes!\
        This tag always uses a 'matches' operator.",
    default=None,
  )
  recording_sample_rate: Optional[SampleRate] = Field(
    serialization_alias='smp',
    description='''
      The smp tag can be used to search for recordings with a specific sampling rate (in Hz).
      For example, smp:">48000" will return hi-res recordings.
      Other frequencies include 22050, 44100 and multiples of 48000.
    ''',
    default=None,
  )
  recording_country: Optional[Country] = Field(
    serialization_alias='cnt',
    title='Country',
    description="To return all recordings that were recorded in the a particular country, use the cnt tag.\
      (...).\
        This field uses a 'starts with' query and accepts a 'matches' operator.",
    examples=[
      {'brazil': 'return all recordings from the country of \"Brazil\"'},
    ],
    default=None,
  )
  
  @field_serializer(
    'recording_latitude',
    'recording_longitude',
    'recording_sample_rate',
  )
  def _serialize_numeric_tag_fields(self, value: search_tags._NumericTag, info):
    if value.constraint is None:
      return f'{value.a}'
    
    match value.constraint:
      case 'at least':
        return f'">{value.a}"'
      
      case 'at most':
        return f'"<{value.a}"'
      
      case 'exactly':
        return f'"={value.a}"'
      case _:
        raise ValueError(value.constraint)
  
  @field_serializer(
    'recording_id',
  )
  def _serialize_recording_id(self, v: Union[RecordingId, str]):
    if isinstance(v, str):
      return v
    
    if v.constraint is None:
      return f'{v.a}'
    
    match v.constraint:
      case 'between':
        if not v.b:
          raise ValueError(v)
        return f'"{v.a:.0f}-{v.b:.0f}"'

      case _:
        return v.a

  @field_serializer(
    'recording_length',
    'recording_temp',
  )
  def _serialize_numeric_range_tag_fields(self, value: search_tags._NumericRangeTag, info):
    if value.constraint is None:
      return f'{value.a}'
    
    match value.constraint:
      case 'at least':
        return f'">{value.a}"'
      
      case 'at most':
        return f'"<{value.a}"'
      
      case 'exactly':
        return f'"={value.a}"'

      case 'between':
        if not value.b:
          raise ValueError(value)
        return f'"{value.a}-{value.b}"'

      case _:
        raise ValueError(value.constraint)

  @field_serializer('recording_country')
  def _serialize_recording_country(self, value: search_tags.Country, info):
    if value is None:
      return None
    return utils.wrap_text(value.country.name.lower())

  # Typed fields
  recording_box: Optional[Box] = Field(
    serialization_alias='box',
    title='Box',
    description="(...) The second tag allows you to search for recordings that occur within a given rectangle,\
      and is called box.\
        It is more versatile than lat and lon, but is more awkward to type in manually,\
          so we have made a map-based search tool to make things simpler.\
            The general format of the box tag is as follows: box:LAT_MIN,LON_MIN,LAT_MAX,LON_MAX.\
              Note that there must not be any spaces between the coordinates.",
    default=None,
  )

  
  @field_serializer('recording_quality')
  def _serialize_recording_quality(self, tag: RecordingQuality):
    q = tag.a.name

    match tag.constraint:
      case None:
        return q
      
      case 'at least':
        if q == 'A':
          return 'A'
        elif q == 'E':
          return None
        else:
          return f'">{QualityRating(tag.a + 1).name}"'
      
      case 'at most':
        if q == 'A':
          return None
        elif q == 'E':
          return 'E'
        else:
          return f'"<{QualityRating(tag.a - 1).name}"'
      
      case _:
        raise ValueError(tag.constraint)

  @field_serializer('recording_since')
  def _serialize_recording_since(self, tag: Since):
    output_format = r'%Y-%m-%d'
    if isinstance(tag.value, datetime):
      return tag.value.strftime(output_format)
    
    elif isinstance(tag.value, timedelta):
      today = datetime.now(timezone.utc)
      lookback = today - tag.value
      return lookback.strftime(output_format)
    
    elif isinstance(tag.value, int):
      return str(tag.value)
    
    raise ValueError(tag)
  
  @field_serializer('recording_box')
  def _serialize_recording_box(self, tag: Box):
    return f'{tag.lat_min},{tag.lon_min},{tag.lat_max},{tag.lon_max}'