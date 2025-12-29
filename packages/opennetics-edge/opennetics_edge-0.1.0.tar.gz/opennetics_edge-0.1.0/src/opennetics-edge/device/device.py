
# device/device.py

#- Imports -----------------------------------------------------------------------------------------

from dataclasses import dataclass

from .input_data import InputData
from .communication import get_data, connect, send_data
from ..typing import numeric_t
from ..file import GestureFile
from ..utils.debug import alert, AlertLevel


#- Local Defines -----------------------------------------------------------------------------------

@dataclass
class GestureRecord:
    gesture: GestureFile
    call: Callable[[], None]
    match: dict[str, int]
    input_index: int
    running: bool = False


#- Device Class ------------------------------------------------------------------------------------

class Device:

    def __init__(self):
        self._input_data: InputData = InputData()       # organised record of read data
        self._gesture_record: list[GestureRecord] = []  # record of all gesture calls


