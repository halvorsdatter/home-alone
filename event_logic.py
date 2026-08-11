# event_logic.py
import time
from config import EVENT_WINDOW_CLOSE_GRACE, EVENT_COOLDOWN

class EventLogic:
    def __init__(self, write_queue):
        self.write_queue    = write_queue
        self.door_state     = "closed"
        self.door_opened_at = None
        self.door_closed_at = None
        self.exit_candidates = {}   # track_id → name; multiple simultaneous exits supported
        self.cooldowns       = {}

    def update(self, snapshot, new_door_state):
        now = time.time()

        if new_door_state != self.door_state:
            if new_door_state == "open":
                self.door_opened_at = now
                for t in snapshot:
                    if (t.name and t.direction() == "approaching_door"
                            and t.in_door_zone()
                            and not self._cooldown(t.name, now)):
                        self.exit_candidates[t.id] = t.name
            elif new_door_state == "closed":
                self.door_closed_at = now
                present = {t.id for t in snapshot if t.disappeared == 0}
                for tid in list(self.exit_candidates):
                    if tid in present:
                        del self.exit_candidates[tid]   # opened door but came back in
            self.door_state = new_door_state

        window = (self.door_state == "open" or
                  (self.door_closed_at and now - self.door_closed_at < EVENT_WINDOW_CLOSE_GRACE))
        if not window:
            self.exit_candidates.clear(); return

        for t in snapshot:
            if t.id in self.exit_candidates and t.disappeared > 5:
                self._fire(self.exit_candidates.pop(t.id), "exit", now)

        for t in snapshot:
            if (t.name and t.identity_locked and t.id not in self.exit_candidates
                    and t.direction() == "entering_apartment" and not t.in_door_zone()
                    and self.door_opened_at and not self._cooldown(t.name, now)):
                self._fire(t.name, "entry", now)

    def _cooldown(self, name, now):
        return now - self.cooldowns.get(name, 0) < EVENT_COOLDOWN

    def _fire(self, name, event_type, now):
        self.cooldowns[name] = now
        is_home = (event_type == "entry")
        print(f"[EVENT] {name} {'entered' if is_home else 'left'}")
        self.write_queue.put({"name": name, "isHome": is_home})