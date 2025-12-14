"""Handler for tile-based targeting (throwing, spells, etc.)."""

from typing import TYPE_CHECKING, Callable, Optional

from bearlibterminal import terminal as blt

from ecs.components import IsPlayer, Position
from ecs.resources import MapResource, TargetModeResource, UIResource
from effects.targeting import is_in_range
from input.input import ActionResult, InputHandler
from ui.popup import PopupStack

if TYPE_CHECKING:
    from ecs.world import World
    from ui.target_panel import TargetMode


class TargetHandler(InputHandler):
    """
    Handles tile-based targeting for throws, spells, etc.

    Features:
    - Cursor movement with arrow keys or vim keys
    - Range validation (cursor shows green if valid, red if out of range)
    - Optional path preview for projectiles
    - Callback-based confirmation
    """

    def __init__(
        self,
        world: "World",
        popup_stack: PopupStack,
        max_range: int,
        radius: int = 0,
        show_path: bool = False,
        on_confirm: Optional[Callable[[int, int], ActionResult]] = None,
        prompt: str = "Select target",
    ):
        """
        Initialize the targeting handler.

        Args:
            world: The game world
            popup_stack: For displaying info popups
            max_range: Maximum targeting range from origin
            radius: AoE radius (0 for single target)
            show_path: Whether to show trajectory line
            on_confirm: Callback when target is confirmed, receives (x, y)
            prompt: Message to display while targeting
        """
        self.world = world
        self.popup_stack = popup_stack
        self.max_range = max_range
        self.radius = radius
        self.show_path = show_path
        self.on_confirm = on_confirm
        self.prompt = prompt

        # Get player position as origin
        players = world.get_entities_with(IsPlayer, Position)
        player = next(iter(players))
        pos: Position = world.component_for(player, Position)

        self.origin_x = pos.x
        self.origin_y = pos.y

        # Initialize or update target mode resource
        target_mode: Optional["TargetMode"] = world.get_resource(TargetModeResource)
        if target_mode:
            target_mode.cursor_x = pos.x
            target_mode.cursor_y = pos.y
            target_mode.origin_x = pos.x
            target_mode.origin_y = pos.y
            target_mode.max_range = max_range
            target_mode.radius = radius
            target_mode.show_path = show_path
        else:
            from ui.target_panel import TargetMode

            world.add_resource(
                TargetModeResource(
                    TargetMode(
                        cursor_x=pos.x,
                        cursor_y=pos.y,
                        origin_x=pos.x,
                        origin_y=pos.y,
                        max_range=max_range,
                        radius=radius,
                        show_path=show_path,
                    )
                )
            )

        super().__init__()

    def load_keybinds(self):
        self.keybinds = {
            # Movement - arrow keys
            blt.TK_UP: lambda: self._move_cursor(0, -1),
            blt.TK_DOWN: lambda: self._move_cursor(0, 1),
            blt.TK_LEFT: lambda: self._move_cursor(-1, 0),
            blt.TK_RIGHT: lambda: self._move_cursor(1, 0),
            # Movement - vim keys
            blt.TK_K: lambda: self._move_cursor(0, -1),
            blt.TK_J: lambda: self._move_cursor(0, 1),
            blt.TK_H: lambda: self._move_cursor(-1, 0),
            blt.TK_L: lambda: self._move_cursor(1, 0),
            blt.TK_Y: lambda: self._move_cursor(-1, -1),
            blt.TK_U: lambda: self._move_cursor(1, -1),
            blt.TK_B: lambda: self._move_cursor(-1, 1),
            blt.TK_N: lambda: self._move_cursor(1, 1),
            # Actions
            blt.TK_ENTER: self._confirm_target,
            blt.TK_ESCAPE: self._cancel,
        }

    def on_enter(self):
        """Activate target mode"""
        target_mode: "TargetMode" = self.world.resource_for(TargetModeResource)
        target_mode.active = True

        # Show targeting prompt
        ui_state = self.world.resource_for(UIResource)
        ui_state.message_log.add(
            f"{self.prompt} (Enter to confirm, Esc to cancel)", "yellow"
        )

    def on_exit(self):
        """Deactivate target mode"""
        target_mode: Optional["TargetMode"] = self.world.get_resource(
            TargetModeResource
        )
        if target_mode:
            target_mode.active = False

    def _move_cursor(self, dx: int, dy: int) -> ActionResult:
        """Move the targeting cursor, clamped to map bounds"""
        target_mode: "TargetMode" = self.world.resource_for(TargetModeResource)
        game_map = self.world.resource_for(MapResource)

        new_x = target_mode.cursor_x + dx
        new_y = target_mode.cursor_y + dy

        # Clamp to map bounds
        new_x = max(0, min(new_x, game_map.width - 1))
        new_y = max(0, min(new_y, game_map.height - 1))

        target_mode.cursor_x = new_x
        target_mode.cursor_y = new_y

        return ActionResult.no_op()

    def _confirm_target(self) -> ActionResult:
        """Confirm the current target location"""
        target_mode: "TargetMode" = self.world.resource_for(TargetModeResource)
        ui_state = self.world.resource_for(UIResource)

        # Check if target is in range
        if not is_in_range(
            self.origin_x,
            self.origin_y,
            target_mode.cursor_x,
            target_mode.cursor_y,
            self.max_range,
        ):
            ui_state.message_log.add("Target is out of range!", "red")
            return ActionResult.no_op()

        # Deactivate targeting before callback
        target_mode.active = False

        # Call the confirmation callback if provided
        if self.on_confirm:
            return self.on_confirm(target_mode.cursor_x, target_mode.cursor_y)

        return ActionResult.pop_handler()

    def _cancel(self) -> ActionResult:
        """Cancel targeting and return to previous handler"""
        ui_state = self.world.resource_for(UIResource)
        ui_state.message_log.add("Targeting cancelled.", "gray")
        return ActionResult.pop_handler()

    def is_valid_target(self, x: int, y: int) -> bool:
        """Check if a tile is a valid target (in range)"""
        return is_in_range(self.origin_x, self.origin_y, x, y, self.max_range)
