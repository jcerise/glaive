from bearlibterminal import terminal

from input.input import ActionResult, InputHandler


class MainGameHandler(InputHandler):
    def __init__(self, player):
        super().__init__()
        self.player = player

    def load_keybinds(self):
        self.keybinds = {
            # Movement - arrow keys
            terminal.TK_UP: self.move_north,
            terminal.TK_DOWN: self.move_south,
            terminal.TK_LEFT: self.move_west,
            terminal.TK_RIGHT: self.move_east,
            # Movement - vim keys
            terminal.TK_K: self.move_north,
            terminal.TK_J: self.move_south,
            terminal.TK_H: self.move_west,
            terminal.TK_L: self.move_east,
            terminal.TK_Y: self.move_northwest,
            terminal.TK_U: self.move_northeast,
            terminal.TK_B: self.move_southwest,
            terminal.TK_N: self.move_southeast,
            # TODO: Actions
            # 'g': self.pickup_item,
            # 'i': self.open_inventory,
            # 'c': self.start_cast_spell,
            # 't': self.start_throw,
            # 'L': self.start_look_mode,  # Capital L for look
            # 'a': self.start_interact,
            # '.': self.wait,
            # ',': self.pickup_item,  # Alternative
        }

    def move_north(self) -> ActionResult:
        return self._move(0, -1)

    def move_south(self) -> ActionResult:
        return self._move(0, 1)

    def move_west(self) -> ActionResult:
        return self._move(-1, 0)

    def move_east(self) -> ActionResult:
        return self._move(1, 0)

    def move_northwest(self) -> ActionResult:
        return self._move(-1, -1)

    def move_northeast(self) -> ActionResult:
        return self._move(1, -1)

    def move_southwest(self) -> ActionResult:
        return self._move(-1, 1)

    def move_southeast(self) -> ActionResult:
        return self._move(1, 1)

    def _move(self, dx: int, dy: int) -> ActionResult:
        success: bool = self.player.try_move(dx, dy)
        if success:
            return ActionResult.turn_passed()

        return ActionResult.no_op()
