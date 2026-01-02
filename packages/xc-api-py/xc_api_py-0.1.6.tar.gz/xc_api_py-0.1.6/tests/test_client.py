from xc_api import Client, SearchQuery, tags
from dotenv import dotenv_values
from rich import print
import pytest
import requests_mock
from xc_api.client import Client, ClientError, ServerError
from xc_api.schemas.search_query import SearchQuery
from xc_api.search_tags import RecordingId

@pytest.fixture
def client():
  env = dotenv_values()
  api_key = env.get('XC_API_KEY')
  if not api_key:
    raise RuntimeError()
  return Client(api_key)

@pytest.fixture
def mock_response():
  """Standard XC API response structure."""
  return {
    "numRecordings": "1",
    "numSpecies": "1",
    "page": 1,
    "numPages": 1,
    "recordings": [
      {
        "id": "12345",
        "gen": "Anas",
        "sp": "platyrhynchos",
        "en": "Mallard",
        "type": "song"
      }
    ]
  }

## --- Method Tests ---

def test_get_by_id_string_parsing(client, mock_response):
  with requests_mock.Mocker() as m:
    m.get('https://xeno-canto.org/api/3/recordings', json=mock_response)
    
    # Test different string formats
    res1 = client.get("XC12345")
    res2 = client.get("xc12345")
    res3 = client.get("12345")
    
    assert res1.id == "12345"
    assert res2.id == "12345"
    assert res3.id == "12345"
    assert m.call_count == 3

def test_get_invalid_id_format(client):
  with pytest.raises(ClientError, match="Invalid XC recording"):
    client.get("invalid-id-format")

def test_find_one_success(client, mock_response):
  with requests_mock.Mocker() as m:
    m.get('https://xeno-canto.org/api/3/recordings', json=mock_response)
    query = SearchQuery(animal_genus="Anas")
    
    recording = client.find_one(query)
    assert recording.id == "12345"
    assert recording.genus == "Anas"

def test_find_pagination_threading(client, mock_response):
  """Tests that ThreadPoolExecutor correctly fetches subsequent pages."""
  multi_page_response = mock_response.copy()
  multi_page_response["numPages"] = 2
  
  with requests_mock.Mocker() as m:
    # Page 1 call
    m.get('https://xeno-canto.org/api/3/recordings?&page=1', json=multi_page_response)
    # Page 2 call
    m.get('https://xeno-canto.org/api/3/recordings?&page=2', json=mock_response)
    
    query = SearchQuery(animal_genus="Anas")
    results = list(client.find(query))
    
    assert len(results) == 2
    assert m.call_count == 2

## --- Error Handling Tests ---

def test_api_401_error(client):
  with requests_mock.Mocker() as m:
    m.get('https://xeno-canto.org/api/3/recordings', status_code=401, json={"message": "Invalid key"})
    
    with pytest.raises(ClientError, match="Invalid key"):
      client.get(12345)

def test_api_400_error(client):
  with requests_mock.Mocker() as m:
    m.get('https://xeno-canto.org/api/3/recordings', status_code=400, json={"message": "Tags only"})
    
    with pytest.raises(ClientError, match="Tags only"):
      client.get(12345)

def test_server_error(client):
  with requests_mock.Mocker() as m:
    m.get('https://xeno-canto.org/api/3/recordings', exc=Exception("Connection Timeout"))
    
    with pytest.raises(ServerError):
      client.get(12345)

def test_lean_validation(client, mock_response):
  """Ensures lean=True uses the LeanRecording model."""
  with requests_mock.Mocker() as m:
    m.get('https://xeno-canto.org/api/3/recordings', json=mock_response)
    
    res = client.get(12345, lean=True)
    # Check that it's actually an instance of LeanRecording vs Recording
    # This assumes LeanRecording is a separate class in your recording.py
    from xc_api.schemas.recording import LeanRecording
    assert isinstance(res, LeanRecording)