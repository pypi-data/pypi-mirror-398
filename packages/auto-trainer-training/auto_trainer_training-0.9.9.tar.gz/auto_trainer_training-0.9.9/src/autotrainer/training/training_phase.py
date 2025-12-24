import math
import uuid
from enum import IntEnum
from typing import List, Dict, Any, Optional, Callable
from typing_extensions import Self

import humps

from .event_slot import EventSlot
from .training_protocols import PredicateContext, TrainingPhaseProtocol, TrainingActionProtocol
from .training_predicate import TrainingPredicate
from .training_action import TrainingAction
from .training_progress import TrainingProgress


class SessionResult(IntEnum):
    NONE = 0
    FALLBACK = 10
    ADVANCE = 20


class TrainingPhase(TrainingPhaseProtocol):
    def __init__(self, phase_id: Optional[str] = None):
        self._phase_id = phase_id or str(uuid.uuid4())
        self._name: str = ""
        self._description: str = ""
        self._fallback_condition: Optional[TrainingPredicate] = None
        self._advance_condition: Optional[TrainingPredicate] = None
        self._session_actions: List[TrainingActionProtocol] = []

        self._is_pellet_delivery_enabled: bool = False
        self._is_pellet_cover_enabled: bool = False
        self._starting_baseline_intensity: int = 0
        self._pellet_hands_min_distance: float = 0.0
        self._is_pellet_shift_enabled: bool = False
        self._is_auto_clamp_enabled: bool = False
        self._auto_clamp_no_activity_release_delay: float = 0.0
        self._auto_clamp_release_load_count: int = 0

        self._progress = TrainingProgress()

        self._would_advance: bool = False
        self._would_fallback: bool = False

        self.property_changed = EventSlot()

    @property
    def phase_id(self) -> str:
        return self._phase_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    @property
    def fallback_predicate(self) -> Optional[TrainingPredicate]:
        return self._fallback_condition

    @fallback_predicate.setter
    def fallback_predicate(self, value: Optional[TrainingPredicate]) -> None:
        self._fallback_condition = value

    @property
    def advance_predicate(self) -> Optional[TrainingPredicate]:
        return self._advance_condition

    @advance_predicate.setter
    def advance_predicate(self, value: Optional[TrainingPredicate]) -> None:
        self._advance_condition = value

    @property
    def session_actions(self) -> List[TrainingActionProtocol]:
        return self._session_actions

    @session_actions.setter
    def session_actions(self, value: List[Callable[[Self, PredicateContext], None]]) -> None:
        self._session_actions = value

    @property
    def progress(self) -> TrainingProgress:
        return self._progress

    @progress.setter
    def progress(self, value: TrainingProgress) -> None:
        self._progress = self._on_property_changed("progress", value, self._progress)

    @property
    def is_pellet_delivery_enabled(self) -> bool:
        return self._is_pellet_delivery_enabled

    @is_pellet_delivery_enabled.setter
    def is_pellet_delivery_enabled(self, value: bool) -> None:
        self._is_pellet_delivery_enabled = value

    @property
    def is_pellet_cover_enabled(self) -> bool:
        return self._is_pellet_cover_enabled

    @is_pellet_cover_enabled.setter
    def is_pellet_cover_enabled(self, value: bool) -> None:
        self._is_pellet_cover_enabled = value

    @property
    def starting_baseline_intensity(self) -> int:
        return self._starting_baseline_intensity

    @starting_baseline_intensity.setter
    def starting_baseline_intensity(self, value: int) -> None:
        self._starting_baseline_intensity = value

    @property
    def pellet_hands_min_distance(self) -> float:
        return self._pellet_hands_min_distance

    @pellet_hands_min_distance.setter
    def pellet_hands_min_distance(self, value: float) -> None:
        self._pellet_hands_min_distance = value

    @property
    def is_pellet_shift_enabled(self) -> bool:
        return self._is_pellet_shift_enabled

    @is_pellet_shift_enabled.setter
    def is_pellet_shift_enabled(self, value: bool) -> None:
        self._is_pellet_shift_enabled = value

    @property
    def is_auto_clamp_enabled(self) -> bool:
        return self._is_auto_clamp_enabled

    @is_auto_clamp_enabled.setter
    def is_auto_clamp_enabled(self, value: bool) -> None:
        self._is_auto_clamp_enabled = value

    @property
    def auto_clamp_no_activity_release_delay(self) -> float:
        return self._auto_clamp_no_activity_release_delay

    @auto_clamp_no_activity_release_delay.setter
    def auto_clamp_no_activity_release_delay(self, value: float) -> None:
        self._auto_clamp_no_activity_release_delay = value

    @property
    def auto_clamp_release_load_count(self) -> int:
        return self._auto_clamp_release_load_count

    @auto_clamp_release_load_count.setter
    def auto_clamp_release_load_count(self, value: int) -> None:
        self._auto_clamp_release_load_count = value

    @property
    def would_advance(self) -> bool:
        return self._would_advance

    @property
    def would_fallback(self) -> bool:
        return self._would_fallback

    def enter(self, context: PredicateContext, is_resume: bool = False) -> None:
        # If is_resume is True, the phase was in progress before this call.  Most likely, it was the active phase when
        # the system was stopped and serialized.  is_resume should not be called as True when started due to fallback
        # or advance, even if it is not the first time in the phase.
        if context.algorithm is not None:
            context.algorithm.reset_configuration()
            context.algorithm.pellet_delivery_enabled = self.is_pellet_delivery_enabled
            context.algorithm.pellet_cover_enabled = self.is_pellet_cover_enabled
            context.algorithm.baseline_intensity = self.starting_baseline_intensity
            context.algorithm.intersession_pellet_shift_enabled = self.is_pellet_shift_enabled

            if self.pellet_hands_min_distance > 0.0:
                context.algorithm.pellet_hands_min_distance = self.pellet_hands_min_distance
            else:
                # Need to explicitly "turn off" since the default might be to have it enabled.
                context.algorithm.pellet_hands_min_distance = math.inf

            context.algorithm.head_fixation_enabled = self.is_auto_clamp_enabled

            if self.auto_clamp_no_activity_release_delay > 0.0:
                context.algorithm.auto_clamp_no_activity_release_delay = self.auto_clamp_no_activity_release_delay

            if self._auto_clamp_release_load_count > 0:
                context.algorithm.auto_clamp_release_load_count = self._auto_clamp_release_load_count

        # TODO Not certain is_resume flag is properly set and considered for all transition types where this is called
        #  (advance vs. fallback vs. resume, etc.) and between loaded existing progress vs. first time in protocol or
        #  phase.

        if not is_resume:
            # Initialize to where things ended from the previous phase.
            if context.pellet_device.last_set_position is not None:
                location = (context.pellet_device.last_set_position.x, context.pellet_device.last_set_position.y,
                            context.pellet_device.last_set_position.z)
            else:
                location = None

            # Advance or fallback resets progress, except, we need to maintain the attempt count.
            self.progress = TrainingProgress(self.progress.phase_attempts + 1, location)

            # Only need an init call if not resuming.  It would overwrite any stored action progress.
            self._perform_session_actions(context, True)
        else:
            if self.progress.pellet_start_location is not None:
                context.pellet_device.set_x(self.progress.pellet_start_location[0])
                context.pellet_device.set_y(self.progress.pellet_start_location[1])
                context.pellet_device.set_z(self.progress.pellet_start_location[2])

        self._evaluate_predicates(context)

    def exit(self, context: PredicateContext) -> None:
        pass

    def session_started(self) -> None:
        self.progress.session_count += 1
        self.progress.progress_resumed()

    def session_ended(self, context: PredicateContext) -> SessionResult:
        self.progress.progress_paused()

        self._perform_session_actions(context)

        return self._evaluate_predicates(context)

    def attach(self, context: PredicateContext):
        if self.progress.phase_attempts == 0 and context.pellet_device.last_set_position is not None:
            self.progress.pellet_start_location = context.pellet_device.last_set_position
            self.progress.pellet_current_location = context.pellet_device.last_set_position

    def _evaluate_predicates(self, context: PredicateContext) -> SessionResult:
        self._would_advance = self._on_property_changed("would_advance", self._should_advance(context),
                                                        self._would_advance)

        self._would_fallback = self._on_property_changed("would_fallback", self._should_fallback(context),
                                                         self._would_fallback)

        if self._would_advance:
            return SessionResult.ADVANCE

        if self._would_fallback:
            return SessionResult.FALLBACK

        return SessionResult.NONE

    def _perform_session_actions(self, context: PredicateContext, is_init: bool = False) -> None:
        # Change delivery locations, magnet intensity, etc... as part of an individual training phase.

        # Actions care about whether it is an initialization call because some actions may be relative to a current
        # value.  For example, progressively move the pellet further way based on the position when the phase is first
        # entered.
        context.progress = self.progress
        for action in self.session_actions:
            action.evaluate(self, context, is_init)

    def _should_fallback(self, context: PredicateContext) -> bool:
        # Check time elapsed too long without enough successful reaches and revert to the last phase, etc.
        context.progress = self.progress
        if self.fallback_predicate is not None:
            return self.fallback_predicate.evaluate(self, context)

        return False

    def _should_advance(self, context: PredicateContext) -> bool:
        context.progress = self.progress
        # Move to the next training phase when any required conditions are met
        if self.advance_predicate is not None:
            return self.advance_predicate.evaluate(self, context) and self._are_actions_complete()

        return False

    def _are_actions_complete(self):
        return all(((not action.has_progress) or action.is_complete) for action in self.session_actions)

    def _on_property_changed(self, property_name, new_value, old_value):
        if old_value == new_value:
            return old_value

        for listener in self.property_changed:
            listener(property_name, new_value, old_value)

        return new_value

    def serialize_progress(self) -> Dict[str, Any]:
        progress = self.progress.to_dict()

        progress["action_context"] = [action.serialize_progress() for action in self.session_actions]

        return progress

    def deserialize_progress(self, progress_item: Dict[str, Any]) -> None:
        self.progress = TrainingProgress.from_dict(progress_item)

        if self.progress.action_context is not None:
            for idx, context in enumerate(self.progress.action_context):
                self.session_actions[idx].deserialize_progress(context)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON serialization"""
        data = {
            "phase_id": self.phase_id,
            "name": self.name,
            "description": self.description,

            "fallback_predicate": self.fallback_predicate.to_dict() if self.fallback_predicate else None,
            "advance_predicate": self.advance_predicate.to_dict() if self.advance_predicate else None,
            "session_actions": [action.to_dict() for action in self.session_actions],

            "is_pellet_delivery_enabled": self.is_pellet_delivery_enabled,
            "is_pellet_cover_enabled": self.is_pellet_cover_enabled,
            "starting_baseline_intensity": self.starting_baseline_intensity,
            "pellet_hands_min_distance": self.pellet_hands_min_distance,
            "is_pellet_shift_enabled": self.is_pellet_shift_enabled,
            "is_auto_clamp_enabled": self.is_auto_clamp_enabled,
            "auto_clamp_no_activity_release_delay": self.is_auto_clamp_enabled,
            "auto_clamp_release_load_count": self.is_auto_clamp_enabled
        }
        return humps.camelize(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Deserialize from dictionary"""
        data = humps.decamelize(data)
        phase = cls(data["phase_id"])
        phase.name = data["name"]
        phase.description = data["description"]

        phase.fallback_predicate = TrainingPredicate.from_dict(data.get("fallback_predicate", None))
        phase.advance_predicate = TrainingPredicate.from_dict(data.get("advance_predicate", None))
        if "session_actions" in data:
            phase.session_actions = [TrainingAction.from_dict(d) for d in data["session_actions"]]
        else:
            phase.session_actions = []

        phase.is_pellet_delivery_enabled = data.get("is_pellet_delivery_enabled", False)
        phase.is_pellet_cover_enabled = data.get("is_pellet_cover_enabled", False)
        phase.starting_baseline_intensity = data.get("starting_baseline_intensity", 5)
        phase.pellet_hands_min_distance = data.get("pellet_hands_min_distance", 0.0)
        phase.is_pellet_shift_enabled = data.get("is_pellet_shift_enabled", False)
        phase.is_auto_clamp_enabled = data.get("is_auto_clamp_enabled", False)
        phase.auto_clamp_no_activity_release_delay = data.get("auto_clamp_no_activity_release_delay", 2.0)
        phase.auto_clamp_release_load_count = data.get("auto_clamp_release_load_count", 5)

        return phase

    def status(self) -> str:
        status = ""

        return status

    def progress_status(self) -> str:
        return self.progress.status()
