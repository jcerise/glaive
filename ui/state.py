from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.layout import LayoutManager
    from ui.log import MessageLog
    from ui.popup import PopupStack


@dataclass
class UIState:
    """Container for all UI state"""

    layout_manager: "LayoutManager"
    popup_stack: "PopupStack"
    message_log: "MessageLog"
