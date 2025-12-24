import time
from datetime import datetime, timezone
from typing import Dict, Tuple, Any, Optional, List
from typing_extensions import Self

import humps

from .event_slot import EventSlot


class TrainingProgress:
    def __init__(self, phase_attempts: int = 0, pellet_start_location: Optional[Tuple[float, float, float]] = None):
        self._phase_attempts: int = phase_attempts
        self._timestamp: Optional[datetime] = None
        self._time_in_training: float = 0.0
        self._session_count: int = 0
        self._pellet_start_location: Optional[Tuple[float, float, float]] = pellet_start_location
        self._pellet_current_location: Optional[Tuple[float, float, float]] = pellet_start_location
        self._pellets_presented: int = 0
        self._pellets_consumed: int = 0
        self._successful_reaches: int = 0
        self._action_context: List[Dict[str, Any]] = []
        self._user_context: Dict[str, Any] = {}

        # TODO Timestamp for first attempt, another for current attempt if more than one.  Also, history of progress for
        #  each attempt.

        self._current_timer: float = 0.0

        self.property_changed = EventSlot()

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: datetime) -> None:
        self._timestamp = self._on_property_changed("timestamp", value, self._timestamp)

    @property
    def time_in_training(self) -> float:
        running = 0 if self._current_timer == 0.0 else time.time() - self._current_timer
        return self._time_in_training + running

    @time_in_training.setter
    def time_in_training(self, value: float) -> None:
        self._time_in_training = self._on_property_changed("time_in_training", value, self._time_in_training)

    @property
    def session_count(self) -> int:
        return self._session_count

    @session_count.setter
    def session_count(self, value: int) -> None:
        self._session_count = self._on_property_changed("session_count", value, self._session_count)

    @property
    def pellets_presented(self) -> int:
        return self._pellets_presented

    @pellets_presented.setter
    def pellets_presented(self, value: int) -> None:
        self._pellets_presented = self._on_property_changed("pellets_presented", value, self._pellets_presented)

    @property
    def pellets_consumed(self) -> int:
        return self._pellets_consumed

    @pellets_consumed.setter
    def pellets_consumed(self, value: int) -> None:
        self._pellets_consumed = self._on_property_changed("pellets_consumed", value, self._pellets_consumed)

    @property
    def pellet_start_location(self) -> Tuple[float, float, float]:
        return self._pellet_start_location

    @pellet_start_location.setter
    def pellet_start_location(self, value: Tuple[float, float, float]) -> None:
        self._pellet_start_location = self._on_property_changed("pellet_start_location", value,
                                                                self._pellet_start_location)

    @property
    def pellet_current_location(self) -> Tuple[float, float, float]:
        return self._pellet_current_location

    @pellet_current_location.setter
    def pellet_current_location(self, value: Tuple[float, float, float]) -> None:
        self._pellet_current_location = self._on_property_changed("pellet_current_location", value,
                                                                  self._pellet_current_location)

    @property
    def successful_reaches(self) -> int:
        return self._successful_reaches

    @successful_reaches.setter
    def successful_reaches(self, value: int) -> None:
        self._successful_reaches = self._on_property_changed("successful_reaches", value, self._successful_reaches)

    @property
    def phase_attempts(self) -> int:
        return self._phase_attempts

    @phase_attempts.setter
    def phase_attempts(self, value: int) -> None:
        self._phase_attempts = self._on_property_changed("phase_attempts", value, self._phase_attempts)

    @property
    def action_context(self) -> List[Dict[str, Any]]:
        return self._action_context

    @action_context.setter
    def action_context(self, value: List[Dict[str, Any]]) -> None:
        self._action_context = value

    @property
    def user_context(self) -> Dict[str, Any]:
        return self._user_context

    @user_context.setter
    def user_context(self, value: Dict[str, Any]) -> None:
        self._user_context = value

    def progress_resumed(self):
        if self._timestamp is None:
            self.timestamp = datetime.now(tz=timezone.utc)

        self._current_timer = time.time()

    def progress_paused(self):
        self.time_in_training += time.time() - self._current_timer

        self._current_timer = 0.0

    def _on_property_changed(self, property_name, new_value, old_value):
        if old_value == new_value:
            return old_value

        for listener in self.property_changed:
            listener(property_name, new_value, old_value)

        return new_value

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON serialization"""
        data = {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "time_in_training": self.time_in_training,
            "session_count": self.session_count,
            "pellets_consumed": self.pellets_consumed,
            "pellet_start_location": list(self.pellet_start_location) if self.pellet_start_location else None,
            "pellet_current_location": list(self.pellet_current_location) if self._pellet_current_location else None,
            "successful_reaches": self.successful_reaches,
            "phase_attempts": self.phase_attempts,
            "action_context": None,
            "user_context": self.user_context
        }
        return humps.camelize(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Deserialize from dictionary"""
        data = humps.decamelize(data)
        progress = cls()
        progress.timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        progress.time_in_training = float(data["time_in_training"])
        progress.session_count = int(data["session_count"])
        progress.pellets_consumed = int(data["pellets_consumed"])

        location: List[float] = data.get("pellet_start_location")
        if location is not None:
            progress.pellet_start_location = tuple(location)
        else:
            progress.pellet_start_location = None

        location: List[float] = data.get("pellet_current_location")
        if location is not None:
            progress.pellet_current_location = tuple(location)
        else:
            progress.pellet_current_location = None

        progress.successful_reaches = int(data.get("successful_reaches", 0))
        progress.phase_attempts = int(data.get("phase_attempts", 0))
        progress.action_context = data.get("action_context", None)
        progress.user_context = data.get("user_context", {})

        return progress

    def status(self) -> str:
        status = ""

        def add_line(line: str) -> None:
            nonlocal status
            status += f"{line}\n"

        def add_prop(line: str) -> None:
            add_line(f"  {line}")

        add_prop(f"Start: {self.timestamp}")
        add_prop(f"Attempts: {self.phase_attempts}")
        add_prop(f"Sessions: {self.session_count}")
        add_prop(f"Pellets presented: {self.pellets_presented}")
        add_prop(f"Pellets consumed: {self.pellets_consumed}")
        add_prop(f"Reaches: {self.successful_reaches}")

        return status
