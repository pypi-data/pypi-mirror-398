from .schemas.search_query import SearchQuery
from .schemas.recording import Recording, LeanRecording
from .schemas.search_response import SearchResponse
from .search_tags import *
from concurrent.futures import (
  ThreadPoolExecutor,
  as_completed,
)
from typing import (
  Optional,
  Iterator,
)
import warnings
from random import randint
import requests
import requests_cache
import re

class ClientError(RuntimeError): ...

class ServerError(RuntimeError): ...

class Client:
  """
  Python client for the [Xeno-Canto API](https://xeno-canto.org/explore/api) (version 3).
  """
  
  _BASE_URL = 'https://xeno-canto.org/api/3'
  _PER_PAGE_MIN = 50
  _PER_PAGE_MAX = 500
  _MAX_WORKERS = 1

  def __init__(self, api_key: str, cache_age: Optional[timedelta] = None):
    self._api_key = api_key
    if cache_age:
      self._session = requests_cache.CachedSession(
        'xc_api_client',
        expire_after=cache_age.total_seconds()
      )
    else:
      self._session = requests.Session()


  def _fetch_by_page(self, query: SearchQuery, per_page: int, page: int, lean: bool = False) -> SearchResponse:
    if per_page < self._PER_PAGE_MIN or per_page > self._PER_PAGE_MAX:
      raise ValueError(per_page)
    
    if page < 1:
      raise ValueError(page)
    
    query_dict = query.model_dump(
      by_alias=True,
      exclude_none=True,
    )
    
    query_string = '+'.join(f'{k}:{v}' for k, v in query_dict.items())
    
    params = dict(
      key=self._api_key,
      per_page=per_page,
      page=page,
      query=query_string,
    )

    params_string = '&'.join(f'{k}={v}' for k, v in params.items())
    
    url = f'{self._BASE_URL}/recordings?{params_string}'
    resp = self._session.get(url)
    
    match resp.status_code:
      case 401:
        body = resp.json()
        msg = body.get(
          'message',
          "Missing or invalid 'key' parameter. Visit https://xeno-canto.org/account to retrieve your API key.",
        )
        raise ClientError(msg) from None
 
      case 400:
        body = resp.json()
        msg = body.get(
          'message',
          "Xeno-canto API v3 only accepts queries using tags. Visit https://xeno-canto.org/explore/api for a complete list."
        )
        raise ClientError(f'{msg} ({resp.url})') from None

      case 503:
        raise ServerError(
          f'Server responded with 503, you probably hit the rate-limit: https://xeno-canto.org/explore/api'
        ) from None
    
    resp.raise_for_status()
    
    if lean:
      return SearchResponse[LeanRecording].model_validate_json(resp.text)
    
    else:
      return SearchResponse[Recording].model_validate_json(resp.text)
  
  def find(self, query: SearchQuery, limit: Optional[int] = None, lean: bool = False) -> Union[Iterator[Recording], Iterator[LeanRecording]]:
      """
      Search for recordings matching a specific query.

      :param query: A SearchQuery object containing the filters to apply.
      :type query: SearchQuery
      :param limit: The maximum number of recordings to return. If None, returns all matches.
      :type limit: Optional[int]
      :return: An iterator yielding Recording objects.
      :rtype: Iterator[Recording]
      :raises ValueError: If limit is less than 1.
      """
      if limit:
        if limit < 1:
          raise ValueError(limit)
        
        elif limit <= self._PER_PAGE_MIN:
          per_page = self._PER_PAGE_MIN
        
        else:
          per_page = self._PER_PAGE_MAX
      
      else:
        per_page = self._PER_PAGE_MAX
      
      # Probing Request
      probe = self._fetch_by_page(
        query=query,
        per_page=per_page,
        page=1,
        lean=lean,
      )
      
      if not probe or not probe.recordings:
        return

      yielded_count = 0
      for recording in probe.recordings:
        yield recording
        yielded_count += 1
        if limit and yielded_count >= limit:
          return

      total_pages = probe.num_pages
      if total_pages <= 1:
        return

      remaining_pages = range(2, total_pages + 1)

      with ThreadPoolExecutor(max_workers=__class__._MAX_WORKERS) as executor:
        # Map page numbers to futures
        future_to_page = {
          executor.submit(self._fetch_by_page, query, per_page, page, lean): page 
          for page in remaining_pages
        }

        for future in as_completed(future_to_page):
          resp = future.result()
          if not resp or not resp.recordings:
            continue

          for recording in resp.recordings:
            yield recording
            yielded_count += 1
            
            if limit and yielded_count >= limit:
              # Cancel pending futures if possible and return
              executor.shutdown(wait=False, cancel_futures=True)
              return

  def find_one(self, query: SearchQuery, lean: bool = False) -> Optional[Union[Recording, LeanRecording]]:
    try:
      recordings = self.find(query, limit=1, lean=lean)
      return next(recordings)
    
    except StopIteration:
      return None

  def get(self, recording_id: str | int, lean: bool = False) -> Optional[Recording | LeanRecording]:
    """
    Retrieve a specific recording by its catalog number.

    :param recording_id: The XC catalog number (e.g., '76967' or 'XC76967').
    :type recording_id: str
    :return: The matching Recording object, or None if no match is found.
    :rtype: Optional[Recording]
    """
    if isinstance(recording_id, str):
      match = re.search(r'(?i:xc)?(?P<id>\d+)', recording_id)
      if not match:
        raise ClientError('Invalid XC recording catalogue number format; See https://xeno-canto.org/explore/api')
      recording_id = match.group('id')
    
    query = SearchQuery(recording_id=RecordingId(int(recording_id)))
    recordings = self.find(query, limit=1, lean=lean)
    
    try:
      return next(recordings)

    except StopIteration:
      warnings.warn(f'No recording found with id "{recording_id}"')
      return None
  
  def sample(self, sample_size: int):
    if sample_size < 1 or sample_size > 100:
      raise ValueError(sample_size)
    
    sample = []
    
    while len(sample) < sample_size:
      xc_id = str(randint(1, 900000))
      
      try:
        sample.append(self.get(xc_id))
      
      except StopIteration:
        continue
    
    return sample