from sys import float_info
from typing import Optional, Dict, Any
from typing_extensions import Self

from .training_protocols import (TrainingActionProtocol, TrainingPhaseProtocol, PredicateContext,
                                 class_from_dict, class_to_dict)

_FLOAT_COMPARISON = float_info.epsilon * 2


class TrainingAction(TrainingActionProtocol):
    @property
    def has_progress(self) -> bool:
        return False

    @property
    def is_complete(self) -> bool:
        return True

    def evaluate(self, phase: TrainingPhaseProtocol, context: PredicateContext, is_init: bool) -> bool:
        return False

    def serialize_progress(self) -> Dict[str, Any]:
        return {}

    def deserialize_progress(self, data: Dict[str, Any]) -> None:
        pass

    def _to_dict(self) -> Optional[Dict[str, Any]]:
        return None

    def to_dict(self) -> Dict[str, Any]:
        return class_to_dict(self.__class__.__name__, self.__class__.__module__, self._to_dict())

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]):
        return class_from_dict(data)


class HeadMagnetIntensityAction(TrainingAction):
    def __init__(self, start: float, increment: float, end: float, pellet_delta: int):
        # Parameters
        self.start = start
        self.increment = increment
        self.end = end
        self.pellet_delta = pellet_delta

        # Internal Progress
        self.pellet_start = 0
        self.current_intensity = 0

    @property
    def has_progress(self) -> bool:
        return True

    @property
    def is_complete(self) -> bool:
        return abs(self.current_intensity) >= self.end - _FLOAT_COMPARISON

    def evaluate(self, phase: TrainingPhaseProtocol, context: PredicateContext, is_init: bool) -> bool:
        if is_init:
            self.pellet_start = context.progress.pellets_consumed
            self.current_intensity = self.start
            # Override any default phase setting
            if context.tunnel_device is not None:
                context.tunnel_device.update_head_magnet_intensity(self.start)
        else:
            if context.progress is None or context.pellet_device is None:
                return False
            if context.progress.pellets_consumed - self.pellet_start > self.pellet_delta:
                intensity = min(self.end, context.tunnel_device.head_magnet_intensity + self.increment)
                self.pellet_start = context.progress.pellets_consumed
                context.tunnel_device.update_head_magnet_intensity(intensity)

        return False

    def serialize_progress(self) -> Dict[str, Any]:
        return {
            "current_intensity": self.current_intensity,
            "pellet_start": self.pellet_start
        }

    def deserialize_progress(self, data: Dict[str, Any]) -> None:
        self.current_intensity = data["current_intensity"]
        self.pellet_start = data["pellet_start"]

    def _to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "increment": self.increment,
            "end": self.end,
            "pellet_delta": self.pellet_delta
        }

    @classmethod
    def from_properties(cls, data: Dict[str, Any]) -> Self:
        start = data["start"]
        increment = data["increment"]
        end = data["end"]
        pellet_delta = data["pellet_delta"]

        return HeadMagnetIntensityAction(start, increment, end, pellet_delta)


class ReachDistanceAction(TrainingAction):
    def __init__(self, increment: float, distance: float, pellet_delta: int):
        # Parameters
        self.increment = increment
        self.distance = distance
        self.pellet_delta = pellet_delta

        # Internal Progress
        self.current_increment_pellet_count = 0
        self.initial_y = 0
        self.current_delta_y = 0
        self.distance_reached_pellet_count = 0

    @property
    def has_progress(self) -> bool:
        return True

    @property
    def _has_reached_distance(self) -> bool:
        return abs(self.current_delta_y) >= self.distance - _FLOAT_COMPARISON

    @property
    def is_complete(self) -> bool:
        if not self._has_reached_distance:
            return False
        if self.distance_reached_pellet_count == 0:
            return False
        return self.current_increment_pellet_count - self.distance_reached_pellet_count >= self.pellet_delta

    def evaluate(self, phase: TrainingPhaseProtocol, context: PredicateContext, is_init: bool) -> bool:
        if is_init:
            self.current_increment_pellet_count = context.progress.pellets_consumed
            if context.pellet_device is not None and context.pellet_device.last_set_position is not None:
                self.initial_y = context.pellet_device.last_set_position.y
            self.current_delta_y = 0
            self.distance_reached_pellet_count = 0
        else:
            if context.progress is None or context.pellet_device is None:
                return False
            if context.progress.pellets_consumed - self.current_increment_pellet_count > self.pellet_delta:
                self.current_increment_pellet_count = context.progress.pellets_consumed
                if not self._has_reached_distance:
                    distance = min(self.distance, context.pellet_device.last_set_position.y + self.increment)
                    self.current_delta_y = distance - self.initial_y
                    context.pellet_device.set_y(distance)
                    if self._has_reached_distance:
                        self.distance_reached_pellet_count = self.current_increment_pellet_count
                elif self.distance_reached_pellet_count == 0:
                    self.distance_reached_pellet_count = self.current_increment_pellet_count

        return False

    def serialize_progress(self) -> Dict[str, Any]:
        return {
            "current_increment_pellet_count": self.current_increment_pellet_count,
            "initial_y": self.initial_y,
            "current_delta_y": self.current_delta_y,
            "distance_reached_pellet_count": self.distance_reached_pellet_count
        }

    def deserialize_progress(self, data: Dict[str, Any]) -> None:
        self.current_increment_pellet_count = data.get("current_increment_pellet_count", 0)
        self.initial_y = data.get("initial_y", 0.0)
        self.current_delta_y = data.get("current_delta_y", 0.0)
        self.distance_reached_pellet_count = data.get("distance_reached_pellet_count", 0)

    def _to_dict(self) -> Dict[str, Any]:
        return {
            "distance": self.distance,
            "increment": self.increment,
            "pellet_delta": self.pellet_delta
        }

    @classmethod
    def from_properties(cls, data: Dict[str, Any]) -> Self:
        distance = data["distance"]
        increment = data["increment"]
        pellet_delta = data["pellet_delta"]

        return ReachDistanceAction(increment, distance, pellet_delta)
