from pydantic import BaseModel


class Rect(BaseModel):
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        """
        Right edge of rectangle (exclusive)
        """
        return self.x + self.width

    @property
    def y2(self) -> int:
        """
        Bottom edge of rectangle (exclusive)
        """
        return self.y + self.height

    @property
    def inner(self) -> "Rect":
        """
        Returns the inner rectangle (excluding the 1 tile border) of this Rect
        """
        return Rect(
            x=self.x + 1, y=self.y + 1, width=self.width - 2, height=self.height - 2
        )

    @property
    def center(self) -> tuple[int, int]:
        """
        Returns the center of this Rect
        """
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains(self, px: int, py: int) -> bool:
        """
        Returns whether or not a given point is contained within this rect
        """
        return self.x <= px < self.x2 and self.y <= py < self.y2

    @staticmethod
    def centered(
        screen_width: int, screen_height: int, popup_width: int, popup_height: int
    ) -> "Rect":
        """
        Create a new rectangle centered on the screen
        """
        x: int = (screen_width - popup_width) // 2
        y: int = (screen_height - popup_height) // 2
        return Rect(x=x, y=y, width=popup_width, height=popup_height)
