import queue

from event_logic import EventLogic


def make(): q = queue.Queue(); return EventLogic(q), q

class T:
    def __init__(self, tid, name, direction, in_zone, disappeared=0):
        self.id = tid; self.name = name; self._d = direction
        self._z = in_zone; self.disappeared = disappeared; self.identity_locked = bool(name)
    def direction(self): return self._d
    def in_door_zone(self): return self._z

def test_exit_fires():
    logic, q = make()
    t = T(1, "Anine", "approaching_door", True)
    logic.update([t], "open"); t.disappeared = 10; logic.update([t], "open")
    assert q.get() == {"name": "Anine", "isHome": False}

def test_no_exit_without_door():
    logic, q = make()
    t = T(1, "Anine", "approaching_door", True)
    logic.update([t], "closed"); t.disappeared = 10; logic.update([t], "closed")
    assert q.empty()

def test_exit_discarded_if_returns():
    logic, q = make()
    t = T(1, "Anine", "approaching_door", True)
    logic.update([t], "open"); t.disappeared = 0; logic.update([t], "closed")
    assert q.empty()

def test_entry_fires():
    logic, q = make()
    logic.update([], "open")
    e = T(2, "Lotte", "entering_apartment", False); logic.update([e], "open")
    assert q.get() == {"name": "Lotte", "isHome": True}

def test_two_exit_simultaneously():
    logic, q = make()
    a = T(1, "Anine", "approaching_door", True)
    b = T(2, "Lotte", "approaching_door", True)
    logic.update([a, b], "open")
    a.disappeared = 10; b.disappeared = 10
    logic.update([a, b], "open")
    events = {q.get()["name"], q.get()["name"]}
    assert events == {"Anine", "Lotte"}

def test_two_enter_simultaneously():
    logic, q = make()
    logic.update([], "open")
    a = T(1, "Anine", "entering_apartment", False)
    b = T(2, "Lotte", "entering_apartment", False)
    logic.update([a, b], "open")
    events = {q.get()["name"], q.get()["name"]}
    assert events == {"Anine", "Lotte"}