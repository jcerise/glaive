from bearlibterminal import terminal

from input.handlers import MainGameHandler
from input.input import InputHandler, InputManager
from terminal.terminal import GlaiveTerminal


class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def draw(self, terminal: GlaiveTerminal):
        terminal.draw(self.x, self.y, "@", "dark red")

    def try_move(self, dx: int, dy: int) -> bool:
        # For now, just check if the player is attempting to move outside the bounds of the terminal
        new_x: int = self.x + dx
        new_y: int = self.y + dy

        width: int = terminal.state(terminal.TK_WIDTH)
        height: int = terminal.state(terminal.TK_HEIGHT)

        if 0 <= new_x < width and 0 <= new_y < height:
            self.x = new_x
            self.y = new_y
            return True

        return False


g_term: GlaiveTerminal = GlaiveTerminal("Glaive", 80, 25)
g_term.init_window()

player: Player = Player(1, 1)
player.draw(g_term)

initial_handler: InputHandler = MainGameHandler(player)
input_manager: InputManager = InputManager(initial_handler)

while True:
    g_term.clear()

    player.draw(g_term)

    event = g_term.handle_event()

    # If a turn is consumed, the game world will update (enemies move, things happen, etc)
    # If a turn is not consumed, the game world is not updated
    turn_consumed: bool = input_manager.process_key(event)

    if turn_consumed:
        # Update the game world, but for now pass
        pass
