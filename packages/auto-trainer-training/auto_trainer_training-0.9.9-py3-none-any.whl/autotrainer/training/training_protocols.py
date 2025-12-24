import importlib
from dataclasses import dataclass
from enum import IntEnum
from typing import Protocol, Optional, Dict, Any

import humps

from autotrainer.behavior.behavior_algorithm import BehaviorAlgorithm
from autotrainer.behavior.pellet_device_protocol import PelletDeviceProtocol
from autotrainer.behavior.tunnel_device_protocol import TunnelDeviceProtocol

from .training_progress import TrainingProgress


# Developer note: The use of protocols in this file name and contents is in reference to Python Protocols _not_ the
# user-facing/medical use of "protocol" in "training protocol".


class TrainingPhaseProtocol(Protocol):
    """
    Defined as a standalone protocol primarily to void circular imports between TrainingPhase and TrainingPredicate.
    """

    @property
    def progress(self) -> TrainingProgress: ...

    @property
    def starting_baseline_intensity(self) -> int: ...

    @property
    def is_pellet_cover_enabled(self) -> bool: ...

    @property
    def is_auto_clamp_enabled(self) -> bool: ...


class TrainingProgressState(IntEnum):
    Unknown = -1
    Initialized = 0
    Active = 10
    Paused = 20
    Failed = 30
    Complete = 40


@dataclass
class PredicateContext:
    progress: Optional[TrainingProgress] = None
    algorithm: Optional[BehaviorAlgorithm] = None
    pellet_device: Optional[PelletDeviceProtocol] = None
    tunnel_device: Optional[TunnelDeviceProtocol] = None


class TrainingActionProtocol(Protocol):
    """
    Defined as a standalone protocol primarily to void circular imports between TrainingPhase and TrainingAction.
    """

    @property
    def has_progress(self) -> bool: ...

    @property
    def is_complete(self) -> bool: ...

    def evaluate(self, phase: TrainingPhaseProtocol, context: PredicateContext, is_init: bool) -> bool: ...

    def serialize_progress(self) -> Dict[str, Any]: ...

    def deserialize_progress(self, data: Dict[str, Any]) -> None: ...

    def to_dict(self) -> Dict[str, Any]: ...

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]): ...


def class_to_dict(name: str, module: str, props: Dict[str, Any]) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "type": name,
        "module": module
    }

    if props:
        data["properties"] = humps.camelize(props)

    return humps.camelize(data)


def class_from_dict(data: Optional[Dict[str, Any]]):
    if data is None:
        return None

    data = humps.decamelize(data)
    module = importlib.import_module(data["module"])
    class_ = getattr(module, data["type"])

    if "properties" in data and getattr(class_, "from_properties"):
        return class_.from_properties(humps.decamelize(data["properties"]))
    else:
        return class_()
