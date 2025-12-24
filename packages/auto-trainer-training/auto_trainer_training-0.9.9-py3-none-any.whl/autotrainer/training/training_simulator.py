import json
from pathlib import Path
from typing import Optional

from autotrainer.behavior import CaptureAnalysisResult
from autotrainer.behavior.behavior_algorithm import BehaviorAlgorithm

from .training_plan import TrainingPlan
from .training_progress import TrainingProgress


class TrainingSimulator:
    """
    A simulation tool for loading, managing, and running TrainingPlan instances with BehaviorAlgorithm integration.
    
    This class provides a high-level interface for:
    - Loading/saving TrainingPlan instances from/to JSON files
    - Loading/saving TrainingProgress data
    - Managing BehaviorAlgorithm attachment to training plans
    - Creating new training plans
    - Resetting progress data
    """

    def __init__(self):
        """Initialize the TrainingSimulator with a new BehaviorAlgorithm instance."""
        self._training_plan: Optional[TrainingPlan] = None
        self._behavior_algorithm: BehaviorAlgorithm = BehaviorAlgorithm()
        self._plan_file_path: Optional[Path] = None
        self._progress_file_path: Optional[Path] = None

    @property
    def behavior_algorithm(self) -> BehaviorAlgorithm:
        """Get the BehaviorAlgorithm instance used by this simulator."""
        return self._behavior_algorithm

    @property
    def training_plan(self) -> Optional[TrainingPlan]:
        """Get the currently loaded TrainingPlan."""
        return self._training_plan

    @property
    def plan_file_path(self) -> Optional[Path]:
        """Get the file path of the currently loaded training plan."""
        return self._plan_file_path

    @property
    def progress_file_path(self) -> Optional[Path]:
        """Get the file path of the currently loaded progress data."""
        return self._progress_file_path

    def load_training_plan(self, file_path: Path) -> None:
        """
        Load a TrainingPlan from a JSON file and attach the BehaviorAlgorithm.
        
        Args:
            file_path: Path to the JSON file containing the training plan
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Training plan file not found: {file_path}")

        # Detach algorithm from current plan if one exists
        if self._training_plan is not None:
            self._training_plan.behavior_algorithm = None

        # Load new plan from file
        self._training_plan = TrainingPlan.from_json_file(file_path)

        # Attach our behavior algorithm to the new plan
        self._training_plan.behavior_algorithm = self._behavior_algorithm

        # Store the file path for future saves
        self._plan_file_path = file_path

        # Clear progress file path as it may no longer be valid
        self._progress_file_path = None

    def load_training_plan_data(self, name: str, data):
        if self._training_plan is not None:
            self._training_plan.behavior_algorithm = None
            self._training_plan.property_changed -= self._on_plan_property_changed

        self._training_plan = TrainingPlan.from_dict(data)
        self._training_plan.property_changed += self._on_plan_property_changed

        self._training_plan.behavior_algorithm = self._behavior_algorithm

        self._plan_file_path = name

        self._progress_file_path = None

    def save_training_plan(self, file_path: Optional[Path] = None) -> None:
        """
        Save the current TrainingPlan to a JSON file.
        
        Args:
            file_path: Optional path to save to. If not provided, uses the stored plan file path.
            
        Raises:
            ValueError: If no training plan is loaded or no file path is available
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded")

        target_path = file_path or self._plan_file_path
        if target_path is None:
            raise ValueError("No file path provided and no stored plan file path available")

        # Serialize the plan to dictionary
        plan_data = self._training_plan.to_dict()

        # Write to JSON file with proper formatting
        with open(target_path, "w") as f:
            json.dump(plan_data, f, indent=2)

        # Update stored file path if a new one was provided
        if file_path is not None:
            self._plan_file_path = file_path

    def load_training_progress(self, file_path: Path) -> None:
        """
        Load training progress data from a JSON file into the current TrainingPlan.
        
        Args:
            file_path: Path to the JSON file containing progress data
            
        Raises:
            ValueError: If no training plan is loaded
            FileNotFoundError: If the file doesn't exist
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded. Load a training plan first.")

        if not file_path.exists():
            raise FileNotFoundError(f"Progress file not found: {file_path}")

        # Use TrainingPlan's built-in progress loading method
        self._training_plan.deserialize_progress_from_file(file_path)

        # Store the file path for future saves
        self._progress_file_path = file_path

    def save_training_progress(self, file_path: Optional[Path] = None) -> None:
        """
        Save the current training progress to a JSON file.
        
        Args:
            file_path: Optional path to save to. If not provided, uses the stored progress file path.
            
        Raises:
            ValueError: If no training plan is loaded or no file path is available
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded")

        target_path = file_path or self._progress_file_path
        if target_path is None:
            raise ValueError("No file path provided and no stored progress file path available")

        # Use TrainingPlan's built-in progress saving method
        self._training_plan.serialize_progress_to_file(target_path)

        # Update stored file path if a new one was provided
        if file_path is not None:
            self._progress_file_path = file_path

    def reset_progress(self) -> None:
        """
        Reset progress data for all phases in the current training plan.
        
        Raises:
            ValueError: If no training plan is loaded
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded")

        # Reset progress for each phase
        for phase in self._training_plan.phases:
            phase.progress = TrainingProgress()

        # Clear stored progress file path as it's no longer valid
        self._progress_file_path = None

    def unload_training_plan(self) -> None:
        """
        Unload the current training plan and detach the BehaviorAlgorithm.
        """
        if self._training_plan is not None:
            self._training_plan.behavior_algorithm = None

        self._training_plan = None
        self._plan_file_path = None
        self._progress_file_path = None

    def start_session(self):
        """
        Convenience method to start a behavior session.

        Raises:
            ValueError: If no training plan is loaded
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded")
        self._behavior_algorithm.start_session()

    def end_session(self):
        """
        Convenience method to end a behavior session.

        Raises:
            ValueError: If no training plan is loaded
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded")
        self._behavior_algorithm.end_session(CaptureAnalysisResult.ANALYSIS_SUCCEEDED)

    def increase_successful_reaches(self, quantity: int = 1) -> None:
        """
        Convenience method to increase successful reaches count.

        Args:
            quantity: Number of successful reaches to add (default: 1)

        Raises:
            ValueError: If no training plan is loaded
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded")
        self._behavior_algorithm.increase_successful_reaches(quantity)

    def increase_pellets_presented(self, quantity: int = 1) -> None:
        """
        Convenience method to increase pellets presented count.

        Args:
            quantity: Number of pellets presented to add (default: 1)

        Raises:
            ValueError: If no training plan is loaded
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded")
        self._behavior_algorithm.increase_pellets_presented(quantity)

    def increase_pellets_consumed(self, quantity: int = 1) -> None:
        """
        Convenience method to increase pellets consumed count.

        Args:
            quantity: Number of pellets consumed to add (default: 1)

        Raises:
            ValueError: If no training plan is loaded
        """
        if self._training_plan is None:
            raise ValueError("No training plan loaded")
        self._behavior_algorithm.increase_pellets_consumed(quantity)

    def info(self) -> str:
        if self.training_plan:
            return "Plan Information\n" + self.training_plan.info()

        return "no training plan loaded"

    def status(self) -> str:
        status = "Simulator Status\n"

        def add_line(line: str) -> None:
            nonlocal status
            status += f"{line}\n"

        add_line(f"Training plan loaded: {'Yes' if self.training_plan else 'No'}")

        add_line(f"Plan file:            {self.plan_file_path or 'None'}")
        add_line(f"Progress file path:   {self.progress_file_path or 'None'}")

        return status

    def progress_status(self) -> str:
        if self.training_plan:
            return "Plan Progress\n" + self.training_plan.progress_status()

        return "no training plan loaded"

    def _on_plan_property_changed(self, name, value, old_value):
        pass
