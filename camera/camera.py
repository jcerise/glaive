class Camera:
    def __init__(self, width: int, height: int, map_width: int, map_height: int):
        self.width: int = width
        self.height: int = height
        self.map_width: int = map_width
        self.map_height: int = map_height

        # Represents the top left corner of the cameras viewport
        self.x: int = 0
        self.y: int = 0

    def update(self, target_x: int, target_y: int) -> None:
        target_camera_x: int = target_x - (self.width // 2)
        target_camera_y: int = target_y - (self.height // 2)

        self.x = self._clamp(target_camera_x, 0, max(0, self.map_width - self.width))
        self.y = self._clamp(target_camera_y, 0, max(0, self.map_height - self.height))

    def world_to_screen(self, world_x: int, world_y: int) -> tuple[int, int]:
        return (world_x - self.x, world_y - self.y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        return (screen_x + self.x, screen_y + self.y)

    def is_visible(self, world_x: int, world_y: int) -> bool:
        return (
            self.x <= world_x < self.x + self.width
            and self.y <= world_y < self.y + self.height
        )

    def get_visible_bounds(self) -> tuple[int, int, int, int]:
        start_x: int = self.x
        start_y: int = self.y
        end_x: int = min(self.x + self.width, self.map_width)
        end_y: int = min(self.y + self.height, self.map_height)
        return (start_x, start_y, end_x, end_y)

    @staticmethod
    def _clamp(value: int, min_value: int, max_value: int) -> int:
        """
        Clamp and integer value between min and max
        """
        return max(min_value, min(value, max_value))
