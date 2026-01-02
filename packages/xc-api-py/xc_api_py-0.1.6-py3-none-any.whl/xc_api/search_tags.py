from abc import ABC
from typing import (
  Optional,
  Union,
)
from datetime import (
  datetime,
  timedelta,
  timezone,
)
from .types import *
from pydantic_core import CoreSchema, core_schema
from pydantic import GetCoreSchemaHandler
import pycountry

_NumericValue = Union[float, int, timedelta]

class _SearchTag(ABC):
  @classmethod
  def __get_pydantic_core_schema__(cls, source_type: type, handler: GetCoreSchemaHandler) -> CoreSchema:
    choices = [
      core_schema.is_instance_schema(cls),  # Allow an instance of this class to pass through without validation
      core_schema.any_schema()              # Allow validation from a dictionary (if needed) or pass to next handler
    ]
    return core_schema.union_schema(
      choices,
      # If you want to use this class as a field *input* type, 
      # you would define a parser/validator here.
    )

class _NumericTag(_SearchTag):
  def __init__(
    self,
    a: _NumericValue,
    b: Optional[_NumericValue] = None,
    constraint: Optional[NumericConstraint] = None,
  ):
    self.a = a
    self.b = b
    self.constraint = constraint

  @classmethod
  def at_least(cls, v: _NumericValue):
    return cls(v, constraint='at least') # f'">{value}"'

  @classmethod
  def at_most(cls, value: _NumericValue):
    return cls(value, constraint='at most') # f'"<{value}"'

  @classmethod
  def exactly(cls, value: _NumericValue):
    return cls(value, constraint='exactly') # f'"={length}"'

class _NumericRangeTag(_NumericTag):
  @classmethod
  def between(cls, a: _NumericValue, b: _NumericValue):
    if not (a and b):
      raise ValueError(f'Need two values')
    
    if not (type(a) is type(b)):
      raise ValueError()

    if a == b:
      raise ValueError(f"Range values must be different: {a}, {b}")
    
    if a > b: # type: ignore
      a, b = b, a
        
    return cls(a, b, constraint='between')

class Length(_NumericRangeTag): ...

class Temp(_NumericRangeTag): ...

class SampleRate(_NumericTag): ...

class Longitude(_NumericTag): ...

class Latitude(_NumericTag): ...

class Quality(_SearchTag):  
  def __init__(
    self,
    value: str,
    contraint: Optional[QualityConstraint] = None,
  ):
    try:
      self.value = RecordingQuality[value.capitalize()]
    
    except:
      values = ', '.join([f'"{r.name}"' for r in RecordingQuality])
      raise ValueError((
        f'Invalid quality "{value}";',
        'Pass one of the following (case-insensitive): ',
        values,
      ))
    self.constraint = contraint

  @classmethod
  def at_least(cls, value: str):
    return cls(value, 'at least') # f'">{value}"'

  @classmethod
  def at_most(cls, value: str):
    return cls(value, 'at most') # f'"<{value}"'

class Country(_SearchTag):
  def __init__(self, country_identifier: str):
    try:
      self.country = pycountry.countries.lookup(country_identifier)
    
    except:
      raise ValueError(f'Invalid country argument "{country_identifier}"; Pass a valid country name or ISO code') \
        from None

class Box(_SearchTag):
  def __init__(
    self,
    lat_min: float,
    lon_min: float,
    lat_max: float,
    lon_max: float
  ):
    self.lat_min = lat_min
    self.lon_min = lon_min
    self.lat_max = lat_max
    self.lon_max = lon_max

class RecordingId(_NumericRangeTag):
  @classmethod
  def at_least(cls, value: _NumericValue):
    raise NotImplementedError()

  @classmethod
  def at_most(cls, value: _NumericValue):
    raise NotImplementedError()

  @classmethod
  def exactly(cls, value: _NumericValue):
    raise NotImplementedError()

class Since(_SearchTag):
  def __init__(self, value: Union[int, timedelta, datetime]):
    self.value = value