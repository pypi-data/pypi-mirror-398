from enum import IntEnum
from sys import float_info
from typing import Protocol, List, Union, Dict, Any, Optional

from typing_extensions import Self

from .training_protocols import PredicateContext, TrainingPhaseProtocol, class_from_dict, class_to_dict

_FLOAT_COMPARISON = float_info.epsilon * 2


class TrainingPredicate(Protocol):
    def evaluate(self, phase: TrainingPhaseProtocol, context: PredicateContext) -> bool:
        return False

    def _to_dict(self) -> Optional[Dict[str, Any]]:
        return None

    def to_dict(self) -> Dict[str, Any]:
        return class_to_dict(self.__class__.__name__, self.__class__.__module__, self._to_dict())

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]):
        return class_from_dict(data)


class CompoundPredicate(TrainingPredicate):
    class CompoundType(IntEnum):
        AND = 0
        OR = 1

    def __init__(self, compound_type: CompoundType, predicates: List[TrainingPredicate]):
        self.compound_type = compound_type
        self.predicates = predicates

    def evaluate(self, phase: TrainingPhaseProtocol, context: PredicateContext) -> bool:
        if self.compound_type == CompoundPredicate.CompoundType.AND:
            return all(predicate.evaluate(phase, context) for predicate in self.predicates)
        else:
            return any(predicate.evaluate(phase, context) for predicate in self.predicates)

    def _to_dict(self) -> Dict[str, Any]:
        return {
            "compound_type": self.compound_type.name,
            "predicates": [predicate.to_dict() for predicate in self.predicates]
        }

    @classmethod
    def from_properties(cls, data: Dict[str, Any]) -> Self:
        compound_type = CompoundPredicate.CompoundType[data["compound_type"]]
        predicates = [TrainingPredicate.from_dict(d) for d in data["predicates"]]

        return CompoundPredicate(compound_type, predicates)


class NumberComparisonPredicate(TrainingPredicate):
    class NumberComparisonType(IntEnum):
        LT = 0
        LTE = 1
        EQ = 2
        GTE = 3
        GT = 4

    def __init__(self, comparison_type: NumberComparisonType, path: str, value: Union[int, float]):
        self.comparison_type = comparison_type
        if not isinstance(path, list):
            self.path = path.split(".")
        else:
            self.path = path
        self.value = value

    def evaluate(self, phase: TrainingPhaseProtocol, context: PredicateContext) -> bool:
        eval_obj = context
        for part in self.path:
            if eval_obj and part:
                if hasattr(eval_obj, part):
                    eval_obj = eval_obj.__getattribute__(part)
                else:
                    eval_obj = None
                    break

        if eval_obj is None:
            return False

        if self.comparison_type == NumberComparisonPredicate.NumberComparisonType.LT:
            return eval_obj < self.value
        elif self.comparison_type == NumberComparisonPredicate.NumberComparisonType.LTE:
            return eval_obj <= self.value
        elif self.comparison_type == NumberComparisonPredicate.NumberComparisonType.EQ:
            if isinstance(eval_obj, float) or isinstance(self.value, float):
                return abs(eval_obj - self.value) < _FLOAT_COMPARISON
            else:
                return eval_obj == self.value
        elif self.comparison_type == NumberComparisonPredicate.NumberComparisonType.GTE:
            return eval_obj >= self.value
        elif self.comparison_type == NumberComparisonPredicate.NumberComparisonType.GT:
            return eval_obj > self.value

        return False

    def _to_dict(self) -> Optional[Dict[str, Any]]:
        return {
            "comparison_type": self.comparison_type.name,
            "path": self.path,
            "value": self.value
        }

    @classmethod
    def from_properties(cls, data: Dict[str, Any]) -> Self:
        comparison_type = NumberComparisonPredicate.NumberComparisonType[data["comparison_type"]]
        path = data["path"]
        value = data["value"]

        return NumberComparisonPredicate(comparison_type, path, value)


class PythonPredicate(TrainingPredicate):
    def __init__(self, python_code: str):
        self.python_code = python_code

    def evaluate(self, phase: TrainingPhaseProtocol, context: PredicateContext) -> bool:
        pass

    def _to_dict(self) -> Optional[Dict[str, Any]]:
        return {
            "python_code": self.python_code
        }

    @classmethod
    def from_properties(cls, data: Dict[str, Any]):
        python_code = data["python_code"]
        return PythonPredicate(python_code)
