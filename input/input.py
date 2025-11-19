class ActionResult:
    """
    Result of an action by the player
    Can result in no action, turn consumption (movement, attacking, etc), or pushing or popping a new keybind set
    onto the input manager stack (opening a menu, or taking a multi-step action)
    """

    def __init__(
        self, consumed_turn: bool = False, push_handler=None, pop: bool = False
    ):
        self.consumed_turn = consumed_turn
        self.push_handler = push_handler
        self.pop = pop

    @staticmethod
    def no_op():
        return ActionResult()

    @staticmethod
    def turn_passed():
        return ActionResult(consumed_turn=True)

    @staticmethod
    def push(handler):
        return ActionResult(push_handler=handler)

    @staticmethod
    def pop_handler():
        return ActionResult(pop=True)

    @staticmethod
    def turn_and_push(handler):
        return ActionResult(consumed_turn=True, push_handler=handler)

    @staticmethod
    def turn_and_pop():
        return ActionResult(consumed_turn=True, pop=True)


class InputHandler:
    """
    Loads keybinds, and handles incoming input events based on those keybinds
    """

    def __init__(self):
        self.keybinds = {}
        self.load_keybinds()

    def load_keybinds(self):
        # Overriden in subclasses
        pass

    def handle_key(self, key) -> ActionResult:
        if key in self.keybinds:
            action = self.keybinds[key]
            return action()

        return self.handle_unbound_key()

    def handle_unbound_key(self) -> ActionResult:
        return ActionResult.no_op()

    def on_enter(self):
        pass

    def on_exit(self):
        pass


class InputManager:
    """
    Manages sets of keybinds, and can add or remove keybind sets (only one set is active at any time, but we can navigate back
    through previous keybinds)
    """

    def __init__(self, initial_handler: InputHandler):
        self.handler_stack: list[InputHandler] = [initial_handler]
        initial_handler.on_enter()

    def current_handler(self) -> InputHandler:
        return self.handler_stack[-1]

    def push_handler(self, handler: InputHandler):
        self.current_handler().on_exit()
        self.handler_stack.append(handler)
        handler.on_enter()

    def pop_handler(self) -> bool:
        if len(self.handler_stack) > 1:
            self.handler_stack.pop().on_exit()
            self.current_handler().on_enter()
            return True

        return False

    def process_key(self, key) -> bool:
        result: ActionResult = self.current_handler().handle_key(key)

        if result.pop:
            self.pop_handler()

        if result.push_handler:
            self.push_handler(result.push_handler)

        return result.consumed_turn
