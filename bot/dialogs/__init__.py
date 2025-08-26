from .common import TEXT as C_TEXT, BUTTONS as C_BTN
from .tires import TIRES_FLOW
from .wheels import WHEELS_FLOW

START_NODE = {
    "start": {
        "text": C_TEXT["choose_entity"],
        "buttons": C_BTN["entity"],
        "next_by_button": {"Шины": "t_entry", "Диски": "w_entry"},
    }
}

FLOW = {
    **START_NODE,
    **TIRES_FLOW,
    **WHEELS_FLOW,
}
