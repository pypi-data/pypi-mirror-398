from pydantic import (
  BaseModel,
  Field,
)
from typing import (
  Sequence,
)
from .recording import Recording

class SearchResponse(BaseModel):
  # model_config = ConfigDict(
  #   populate_by_name=True,
  #   validate_by_alias=True,
  # )
  num_recordings: int = Field(
    alias='numRecordings',
    description='Total recordings fetched via the query',
  )
  num_species: int = Field(
    alias='numSpecies',
    description='Number of species represented in the results',
  )
  page: int = Field(
    alias='page',
    description='Current page number in the query result',
  )
  num_pages: int = Field(
    alias='numPages',
    description='Total pages of recordings fetched via the query',
  )
  recordings: Sequence[Recording] = Field(
    description='List of recording objects on this page',
  )