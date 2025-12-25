class ExecutionContext:
    """
    Carries runtime state and manages intent execution stack.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self._intent_stack = []

    def push_intent(self, frame):
        self._intent_stack.append(frame)

    def pop_intent(self):
        if self._intent_stack:
            return self._intent_stack.pop()

    def current_intent(self):
        return self._intent_stack[-1] if self._intent_stack else None

    def depth(self):
        return len(self._intent_stack)
