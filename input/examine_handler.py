from bearlibterminal import terminal as blt

from input.input import ActionResult, InputHandler
from ui.popup import Popup, PopupStack


class ExamineHandler(InputHandler):
    """
    Simple handler for the examine popup.
    Closes on Escape, Enter, or Space.
    """

    def __init__(self, popup: Popup, popup_stack: PopupStack):
        self.popup = popup
        self.popup_stack = popup_stack
        self._popup_pushed = False
        super().__init__()

    def load_keybinds(self):
        self.keybinds = {
            blt.TK_ESCAPE: self._close,
            blt.TK_ENTER: self._close,
            blt.TK_SPACE: self._close,
        }

    def _close(self) -> ActionResult:
        if self.popup and not self.popup_stack.is_empty():
            self.popup_stack.pop()
        return ActionResult.pop_handler()

    def on_enter(self):
        if self.popup and not self._popup_pushed:
            self.popup_stack.push(self.popup)
            self._popup_pushed = True

    def on_exit(self):
        pass
