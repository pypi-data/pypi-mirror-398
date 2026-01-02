from datetime import datetime, date, time, timedelta
import re
import yarl
from functools import wraps
from typing import Optional

INVALID_STRING_INPUTS = ['', '?', 'unknown']


def handle_invalid_input(func):
  @wraps(func)
  def wrapper(s: str, *args, **kwargs):
    if not isinstance(s, str) or s.lower() in INVALID_STRING_INPUTS:
      return None
    return func(s, *args, **kwargs)
  return wrapper

@handle_invalid_input
def validate_url(s: str) -> yarl.URL:
  if not s.startswith('https:'):
    s = f'https:{s}'
  return yarl.URL(s)

@handle_invalid_input
def validate_float(s: str) -> float:
  return float(s)

@handle_invalid_input
def validate_date(s: str) -> Optional[date]:
  try:
    return datetime.fromisoformat(s)
  
  except:
    return None

@handle_invalid_input
def validate_string(s: str) -> str:
  return s

@handle_invalid_input
def validate_time(s: str) -> time:
  try:
    # 1. Try standard ISO format first (fastest)
    return time.fromisoformat(s)
  
  except ValueError:
    # 2. Handle '6:05' or '18:5' style by parsing specifically
    # %H handles single digits like '6' as '06' automatically
    
    if len(s.split(':')) == 2:
      return datetime.strptime(s, "%H:%M").time()
    
    # elif len(s.split(':')) == 3:
    return datetime.strptime(s, "%H:%M:%S").time()

@handle_invalid_input
def validate_timedelta(s: str) -> timedelta:
  t = datetime.strptime(s, '%M:%S')
  return timedelta(minutes=t.minute, seconds=t.second)

@handle_invalid_input
def validate_boolean(s: str) -> bool:
  if s.lower().startswith('yes'):
    return True
  elif s.lower().startswith('no'):
    return False
  else:
    raise ValueError(s)

def validate_xc_file_upload_url(s: str) -> yarl.URL:
  if s.startswith('//'):
    s = f'https:{s}'
  
  invalid_values = ['', '?', 'unknown']
  if s.lower() in invalid_values:
    raise ValueError(f"Field received an invalid placeholder value: '{s}'")

  PATTERN = (
    r'^https?://xeno-canto\.org/sounds/uploaded'
    r'/(?P<user_id>[^/]+)'
    r'/(?:ffts|wave)' # "ffts"=sonogram, "wave"=oscillogram
    r'/XC(?P<recording_id>\d+)'
    r'-(?P<version>small|med|large|full)'
    r'\.(?P<file_ext>[a-z0-9]+)$'
  )

  match = re.match(PATTERN, s)
  
  if not match:
    raise ValueError(s)
  
  metadata = match.groupdict() # TODO Something with this
  
  return yarl.URL(s)