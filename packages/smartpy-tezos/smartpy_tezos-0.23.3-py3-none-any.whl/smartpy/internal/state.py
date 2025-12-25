class State:
    def __init__(self):
        self.unknownIds = 0
        self.current_scenario = None
        self.runtime = None
        self.canopy = None
        self.oasis = None


_state = None


def init_state():
    global _state
    if _state is not None:
        raise Exception("State already initialized")
    _state = State()


def get_state():
    global _state
    return _state
