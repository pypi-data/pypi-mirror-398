from typing import Literal, TypeAlias
from enum import IntEnum
from datetime import date, time, timedelta

class QualityRating(IntEnum):
  A = 1 # Best
  B = 2
  C = 3
  D = 4
  E = 5 # Worst

NumericConstraint: TypeAlias = Literal[
  'exactly',
  'at least',
  'at most',
  'between',
]

QualityConstraint: TypeAlias = Literal[
  'exactly',
  'at least',
  'at most',
  'between',
]

RecordingArea: TypeAlias = Literal[
  'africa',
  'america',
  'asia',
  'australia',
  'europe',
]

AnimalSex: TypeAlias = Literal[
  'male',
  'female',
]

AnimalLifeStage: TypeAlias = Literal[
  'adult',
  'juvenile',
  'nestling',
  'nymph',
  'subadult',
]

AnimalGroup: TypeAlias = Literal[
  'grasshoppers',
  'bats',
  'birds',
  'frogs',
  'land mammals'
]

AnimalSoundType: TypeAlias = Literal[
  'aberrant',
  'advertisement call',
  'agonistic call',
  'alarm call',
  'begging call',
  'call',
  'calling song',
  'courtship song',
  'dawn song',
  'defensive call',
  'distress call',
  'disturbance song',
  'drumming',
  'duet',
  'echolocation',
  'feeding buzz',
  'female song',
  'flight call',
  'flight song',
  'imitation',
  'mating call',
  'mechanical sound',
  'nocturnal flight call',
  'release call',
  'rivalry song',
  'searching song',
  'social call',
  'song',
  'subsong',
  'territorial call',
]

RecordingMethod: TypeAlias = Literal[
  'emerging from roost',
  'field recording',
  'fluorescent light tag',
  'hand-release',
  'in enclosure',
  'in net',
  'in the hand',
  'roosting',
  'roped',
  'studio recording',
]
