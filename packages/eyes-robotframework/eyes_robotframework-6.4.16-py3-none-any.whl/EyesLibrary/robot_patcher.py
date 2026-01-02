import os
import sys
import time
import traceback
from typing import TYPE_CHECKING, Any

from robot.api import logger as robot_logger
from robot.output.output import Output
from robot.result import ExecutionResult

from EyesLibrary.test_results_manager import EyesResultsProcessor

if TYPE_CHECKING:
    from robot.result.executionresult import Result


class RobotEnvironment:
    """Detects and provides information about the Robot Framework execution environment."""

    @property
    def is_ci(self) -> bool:
        return (
            os.environ.get("CI", "false").lower() == "true"
            or os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"
        )

    @property
    def retry_count(self) -> int:
        return 3 if self.is_ci else 1

    @property
    def retry_delay(self) -> float:
        return 1.0 if self.is_ci else 0.2

    @property
    def is_pabot(self) -> bool:
        return "pabot" in sys.modules

    @property
    def pre_processing_delay(self) -> float:
        return 0.5 if self.is_ci else 0.0


class RobotFrameworkPatcher:
    """
    Handles patching of Robot Framework functions for Eyes integration.

    This class manages patching Robot Framework's output handling to
    intercept and process Eyes test results.
    """

    def __init__(self):
        self.env = RobotEnvironment()
        self.original_output_close = None

    def apply_patches(self) -> None:
        """Apply all necessary patches to Robot Framework."""
        self.original_output_close = Output.close
        Output.close = lambda output_instance, result: self.patched_output_close(
            output_instance, result
        )

        if self.env.is_pabot:
            self.patch_pabot()

    def patch_pabot(self) -> None:
        """Patch Pabot's result merger if Pabot is being used."""
        try:
            import pabot.result_merger
            from pabot.result_merger import merge as original_merge

            def create_patched_merge(patcher_instance, original_fn):
                def patched_merge(*args: Any, **kwargs: Any) -> Any:
                    result = original_fn(*args, **kwargs)

                    if args and os.path.exists(args[0]):
                        merged_output = args[0]

                        if patcher_instance.env.is_ci:
                            time.sleep(1.0)

                        patcher_instance.process_output_file(merged_output)

                    return result

                return patched_merge

            patched_merge = create_patched_merge(self, original_merge)
            pabot.result_merger.merge = patched_merge

        except ImportError:
            pass
        except Exception as e:
            robot_logger.console(f"Failed to patch pabot's result_merger: {str(e)}")

    def patched_output_close(self, output_instance, result: "Result") -> Any:
        close_result = self.original_output_close(output_instance, result)

        if hasattr(output_instance, "_settings") and hasattr(
            output_instance._settings, "output"
        ):
            output_path = output_instance._settings.output
            self.process_output_file(output_path)

        return close_result

    def process_output_file(self, output_path: str) -> bool:
        if not os.path.exists(output_path):
            return False

        if self.env.pre_processing_delay > 0:
            time.sleep(self.env.pre_processing_delay)

        for attempt in range(self.env.retry_count):
            try:
                full_results = ExecutionResult(output_path)
                processed = EyesResultsProcessor.process_results(full_results)

                if processed:
                    full_results.save(output_path)
                    return True
                return False

            except Exception as e:
                if attempt < self.env.retry_count - 1:
                    time.sleep(self.env.retry_delay)

        return False


# Create an instance of RobotFrameworkPatcher and apply patches
patcher = RobotFrameworkPatcher()
patcher.apply_patches()
