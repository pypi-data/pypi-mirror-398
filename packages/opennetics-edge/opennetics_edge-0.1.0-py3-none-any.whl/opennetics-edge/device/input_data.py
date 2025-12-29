
# device/input_data.py

#- Imports -----------------------------------------------------------------------------------------

from dataclasses import dataclass

from ..typing import numeric_t
from ..utils.debug import alert


#- Local Defines -----------------------------------------------------------------------------------

@dataclass
class Record:
    timestamp: float
    reading: list[numeric_t]


#- InputData Class ---------------------------------------------------------------------------------

class InputData:

    def __init__(self):
        self._data_record: list[Record] = []   # [( time: data_read )]


