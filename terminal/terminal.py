from bearlibterminal import terminal as blt

from terminal.glyph import Glyph


class GlaiveTerminal:
    """
    A convenience wrapper around BearLibTerminal's Python API. Cleans up the API by combining multiple calls into single methods.
    """

    def __init__(
        self,
        window_name: str,
        window_width: int,
        window_height: int,
        compose_tiles: bool = False,
    ):
        self.window_name = window_name
        self.window_width = window_width
        self.window_height = window_height
        self.compose_tiles = compose_tiles

    def init_window(self):
        # Initialize the window with the given dimensions, name, and composition settings
        blt.open()
        blt.set(
            f"window: size={self.window_width}x{self.window_height}, title='{self.window_name}'"
        )
        blt.composition(self.compose_tiles)
        blt.color(blt.color_from_name("white"))
        blt.refresh()

    def handle_event(self) -> int:
        # Handle user input events
        event = blt.read()
        if event == blt.TK_CLOSE or event == blt.TK_ESCAPE:
            blt.close()
            return event
        else:
            return event

    def draw(self, x: int, y: int, char: str, color: str, bk_color: str = "black"):
        blt.color(blt.color_from_name(color))
        blt.bkcolor(blt.color_from_name(bk_color))
        blt.put(x, y, char)
        blt.bkcolor(blt.color_from_name("black"))

    def draw_glyph(self, x: int, y: int, glyph: Glyph):
        blt.color(blt.color_from_name(glyph.fg_color))
        blt.bkcolor(blt.color_from_name(glyph.bg_color))
        blt.put(x, y, glyph.char)
        blt.bkcolor(blt.color_from_name("black"))

    def draw_string(self, x: int, y: int, string: str, color: str):
        blt.color(blt.color_from_name(color))
        blt.printf(x, y, string)
        blt.refresh()

    def clear(self):
        blt.clear()

    def refresh(self):
        blt.refresh()

    def set_layer(self, layer: int):
        blt.layer(layer)

    def draw_at_layer(self, x: int, y: int, glyph: Glyph, layer: int):
        blt.layer(layer)
        self.draw_glyph(x, y, glyph)
        blt.layer(0)

    def draw_string_at_layer(self, x: int, y: int, string: str, color: str, layer: int):
        blt.layer(layer)
        self.draw_string(x, y, string, color)
        blt.layer(0)

    def clear_layer(self, layer: int):
        blt.layer(layer)
        blt.clear_area(0, 0, self.window_width, self.window_height)
        blt.layer(0)
