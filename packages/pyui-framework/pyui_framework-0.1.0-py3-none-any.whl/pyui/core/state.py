class State:
    def __init__(self, value):
        self._value = value
        self._subscribers = []

    def get(self):
        return self._value

    def set(self, new_value):
        self._value = new_value
        for callback in self._subscribers:
            callback()

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def __str__(self):
        return str(self._value)
