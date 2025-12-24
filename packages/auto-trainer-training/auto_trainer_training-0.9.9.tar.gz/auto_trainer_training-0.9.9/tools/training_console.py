#!/usr/bin/env python3
"""
Interactive console application for controlling TrainingSimulator objects.

This console provides command-line interface to load, save, and manipulate
training plans and progress data using the TrainingSimulator class.
"""

import json
from pathlib import Path
from typing import List

from autotrainer.training.training_simulator import TrainingSimulator


class TrainingConsole:
    """Interactive console for controlling TrainingSimulator instances."""

    def __init__(self):
        """Initialize the console with a new TrainingSimulator instance."""
        self.simulator = TrainingSimulator()
        self.last_command = ""
        self.running = True

    def run(self) -> None:
        """Run the main console loop."""
        print("Training Console - Interactive TrainingSimulator Control")
        print("Type 'help' or '?' for available commands, 'quit' to exit")
        print()

        while self.running:
            try:
                line = input(f"training> ").strip()

                # Allow repeating last command with empty input
                if not line and self.last_command:
                    line = self.last_command
                    print(f"(repeating: {line})")

                if line:
                    self.last_command = line
                    self.process_command(line)

            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break
            except Exception as error:
                print(f"Unexpected error: {error}")
                print("Type 'help' for available commands.")

    def process_command(self, command_line: str) -> None:
        """Parse and execute a command."""
        parts = command_line.split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        # Command dispatch
        command_map = {
            "help": self.cmd_help,
            "?": self.cmd_help,
            "quit": self.cmd_quit,
            "exit": self.cmd_quit,
            "status": self.cmd_status,
            "load": self.cmd_load_plan,
            "save": self.cmd_save_plan,
            "load_progress": self.cmd_load_progress,
            "save_progress": self.cmd_save_progress,
            "reset_progress": self.cmd_reset_progress,
            "start_session": self.cmd_start_session,
            "end_session": self.cmd_end_session,
            "inc_reaches": self.cmd_inc_reaches,
            "inc_presented": self.cmd_inc_presented,
            "inc_consumed": self.cmd_inc_consumed,
            "info": self.cmd_info,
            "progress": self.cmd_progress,
        }

        if command in command_map:
            command_map[command](args)
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")

    def cmd_help(self, args: List[str]) -> None:
        """Display help information."""
        print("Available commands:")
        print()
        print("File Operations:")
        print("  load_plan <filepath>       Load a training plan from JSON file")
        print("  save_plan [filepath]       Save current training plan to JSON file")
        print("  load_progress <filepath>   Load training progress from JSON file")
        print("  save_progress [filepath]   Save current training progress to JSON file")
        print()
        print("Training Control:")
        print("  reset_progress             Reset all progress data in current plan")
        print("  inc_reaches [quantity]     Increase successful reaches count (default: 1)")
        print("  inc_presented [quantity]   Increase pellets presented count (default: 1)")
        print("  inc_consumed [quantity]    Increase pellets consumed count (default: 1)")
        print()
        print("Information:")
        print("  status                     Show simulator status")
        print("  info                       Display current training plan details")
        print("  progress                   Display current progress statistics")
        print()
        print("Utility:")
        print("  help, ?                    Show this help message")
        print("  quit, exit                 Exit the console")
        print()
        print("Notes:")
        print("  - Press Enter without typing to repeat the last command")
        print("  - File paths can be relative or absolute")

    def cmd_quit(self, args: List[str]) -> None:
        """Exit the console."""
        self.running = False

    def cmd_load_plan(self, args: List[str]) -> None:
        """Load a training plan from a JSON file."""
        if not args:
            print("Error: load_plan requires a file path")
            print("Usage: load_plan <filepath>")
            return

        try:
            file_path = Path(args[0]).resolve()
            self.simulator.load_training_plan(file_path)
            print(f"Successfully loaded training plan from: {file_path}")
            if self.simulator.training_plan:
                print(f"Plan name: {self.simulator.training_plan.name or 'Unnamed'}")
                print(f"Number of phases: {len(self.simulator.training_plan.phases)}")
        except FileNotFoundError:
            print(f"Error: File not found: {args[0]}")
        except PermissionError:
            print(f"Error: Permission denied accessing: {args[0]}")
        except json.JSONDecodeError as error:
            print(f"Error: Invalid JSON in file: {error}")
        except Exception as error:
            print(f"Error loading training plan: {error}")

    def cmd_save_plan(self, args: List[str]) -> None:
        """Save the current training plan to a JSON file."""
        try:
            file_path = Path(args[0]).expanduser().resolve() if args else None
            self.simulator.save_training_plan(file_path)
            target_path = file_path or self.simulator.plan_file_path
            print(f"Successfully saved training plan to: {target_path}")
        except ValueError as error:
            print(f"Error: {error}")
            if not args:
                print("Usage: save_plan <filepath>")
        except PermissionError:
            file_arg = args[0] if args else "current path"
            print(f"Error: Permission denied writing to: {file_arg}")
        except Exception as error:
            print(f"Error saving training plan: {error}")

    def cmd_load_progress(self, args: List[str]) -> None:
        """Load training progress from a JSON file."""
        if not args:
            print("Error: load_progress requires a file path")
            print("Usage: load_progress <filepath>")
            return

        try:
            file_path = Path(args[0]).expanduser().resolve()
            self.simulator.load_training_progress(file_path)
            print(f"Successfully loaded training progress from: {file_path}")
        except ValueError as error:
            print(f"Error: {error}")
        except FileNotFoundError:
            print(f"Error: File not found: {args[0]}")
        except PermissionError:
            print(f"Error: Permission denied accessing: {args[0]}")
        except json.JSONDecodeError as error:
            print(f"Error: Invalid JSON in file: {error}")
        except Exception as error:
            print(f"Error loading training progress: {error}")

    def cmd_save_progress(self, args: List[str]) -> None:
        """Save the current training progress to a JSON file."""
        try:
            file_path = Path(args[0]).expanduser().resolve() if args else None
            self.simulator.save_training_progress(file_path)
            target_path = file_path or self.simulator.progress_file_path
            print(f"Successfully saved training progress to: {target_path}")
        except ValueError as error:
            print(f"Error: {error}")
            if not args:
                print("Usage: save_progress <filepath>")
        except PermissionError:
            file_arg = args[0] if args else "current path"
            print(f"Error: Permission denied writing to: {file_arg}")
        except Exception as error:
            print(f"Error saving training progress: {error}")

    def cmd_reset_progress(self, args: List[str]) -> None:
        """Reset all progress data in the current training plan."""
        if not self.simulator.training_plan:
            print("Error: No training plan loaded. Load a plan first.")
            return

        # Ask for confirmation
        try:
            response = input("Are you sure you want to reset all progress data? (y/N): ").strip().lower()
            if response in ["y", "yes"]:
                self.simulator.reset_progress()
                print("Progress data has been reset for all phases.")
            else:
                print("Reset cancelled.")
        except (KeyboardInterrupt, EOFError):
            print("\nReset cancelled.")

    def cmd_start_session(self, args: List[str]) -> None:
        """Start behavior session."""
        if not self.simulator.training_plan:
            print("Error: No training plan loaded. Load a plan first.")
            return
        self.simulator.start_session()

    def cmd_end_session(self, args: List[str]) -> None:
        """End behavior session."""
        if not self.simulator.training_plan:
            print("Error: No training plan loaded. Load a plan first.")
            return
        self.simulator.end_session()

    def cmd_inc_reaches(self, args: List[str]) -> None:
        """Increase successful reaches count."""
        if not self.simulator.training_plan:
            print("Error: No training plan loaded. Load a plan first.")
            return

        quantity = 1
        if args:
            try:
                quantity = int(args[0])
                if quantity <= 0:
                    print("Error: Quantity must be a positive integer")
                    return
            except ValueError:
                print("Error: Invalid quantity. Must be a positive integer.")
                return

        try:
            self.simulator.increase_successful_reaches(quantity)
            print(f"Increased successful reaches by {quantity}")
        except Exception as error:
            print(f"Error: {error}")

    def cmd_inc_presented(self, args: List[str]) -> None:
        """Increase pellets presented count."""
        if not self.simulator.training_plan:
            print("Error: No training plan loaded. Load a plan first.")
            return

        quantity = 1
        if args:
            try:
                quantity = int(args[0])
                if quantity <= 0:
                    print("Error: Quantity must be a positive integer")
                    return
            except ValueError:
                print("Error: Invalid quantity. Must be a positive integer.")
                return

        try:
            self.simulator.increase_pellets_presented(quantity)
            print(f"Increased pellets presented by {quantity}")
        except Exception as error:
            print(f"Error: {error}")

    def cmd_inc_consumed(self, args: List[str]) -> None:
        """Increase pellets consumed count."""
        if not self.simulator.training_plan:
            print("Error: No training plan loaded. Load a plan first.")
            return

        quantity = 1
        if args:
            try:
                quantity = int(args[0])
                if quantity <= 0:
                    print("Error: Quantity must be a positive integer")
                    return
            except ValueError:
                print("Error: Invalid quantity. Must be a positive integer.")
                return

        try:
            self.simulator.increase_pellets_consumed(quantity)
            print(f"Increased pellets consumed by {quantity}")
        except Exception as error:
            print(f"Error: {error}")

    def cmd_status(self, args: List[str]) -> None:
        """Display current simulator status."""
        print("---------------------------------\n")
        print(self.simulator.status())
        print("---------------------------------\n")

    def cmd_info(self, args: List[str]) -> None:
        """Display detailed information about the current training plan."""
        print("---------------------------------\n")
        print(self.simulator.info())
        print("---------------------------------\n")

    def cmd_progress(self, args: List[str]) -> None:
        """Display current progress statistics."""
        print("---------------------------------\n")
        print(self.simulator.progress_status())
        print("---------------------------------\n")


def main():
    """Main entry point for the training console application."""
    console = TrainingConsole()
    console.run()


if __name__ == "__main__":
    main()
