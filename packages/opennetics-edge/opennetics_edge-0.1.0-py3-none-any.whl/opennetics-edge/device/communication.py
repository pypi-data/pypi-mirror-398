
# device/communication.py

#- Imports -----------------------------------------------------------------------------------------

from typing import Any

from ..typing import numeric_t
from ..utils.debug import alert, AlertLevel


#- Public Calls ------------------------------------------------------------------------------------

# placeholder: implement device connection
def connect(username: str, password:str) -> bool:
    return True


# placeholder: implement to get data from the source and return as numeric str
def get_data() -> list[numeric_t]:
    Result: list[numeric_t] = []
    return Result


# placeholder: implement to send data to the device. Add more args to specify device n stuff
def send_data(data: Any) -> None:
    # if fail
    try:
        pass

    except Exception as e:
        alert(f"failed to send data. {e}", backtrack=3, level=AlertLevel.ERROR)
        # backtrack=3 because:
        #   backtrack=0 is the code in alert() function
        #   backtrack=1 is this call
        #   backtrack=2 is in Devices.write(), where this procedure was called
        #   backtrack=3 is where Devices.write() method was called

