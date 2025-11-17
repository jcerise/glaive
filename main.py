from bearlibterminal import terminal

from terminal.terminal import GlaiveTerminal


class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def draw(self, terminal: GlaiveTerminal):
        terminal.draw(self.x, self.y, "@", "dark red")


g_term: GlaiveTerminal = GlaiveTerminal("Glaive", 80, 25)
g_term.init_window()

player: Player = Player(1, 1)
player.draw(g_term)

while event := g_term.handle_event():
    g_term.clear()

    if event == terminal.TK_UP:
        player.y -= 1
    elif event == terminal.TK_DOWN:
        player.y += 1
    elif event == terminal.TK_LEFT:
        player.x -= 1
    elif event == terminal.TK_RIGHT:
        player.x += 1

    player.draw(g_term)
