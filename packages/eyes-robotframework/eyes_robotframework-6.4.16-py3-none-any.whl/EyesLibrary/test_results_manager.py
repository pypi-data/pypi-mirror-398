from __future__ import absolute_import, unicode_literals

import json
import os
import tempfile
import time
import uuid
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    List,
    Optional,
    Text,
    TypeVar,
    Union,
)

from robot.api import logger as robot_logger
from robot.result import Keyword


def format_timestamp():
    """
    Create a properly formatted timestamp for Robot Framework messages.
    """
    try:
        # Default get_timestamp function uses format that isn't always compatible
        # Format to proper ISO format instead
        return datetime.now().replace(microsecond=0).isoformat(" ")
    except Exception as e:
        robot_logger.debug(f"Error formatting timestamp: {str(e)}")
        # Fallback to a guaranteed format that works with Robot
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


from applitools.common.test_results import TestResultsStatus

from .keywords_list import CHECK_KEYWORDS_LIST

if TYPE_CHECKING:
    from robot.result.executionresult import Result
    from robot.running import TestSuite

    from applitools.common import TestResults, TestResultsSummary
    from EyesLibrary.config import RobotConfiguration

__all__ = [
    "EyesToRobotTestResultsManager",
    "SuitePostProcessManager",
    "EyesResultsProcessor",
]

EYES_STATUS_TO_ROBOT_STATUS = {
    TestResultsStatus.Passed: "PASS",
    TestResultsStatus.Failed: "FAIL",
    TestResultsStatus.Unresolved: "FAIL",
}
METADATA_PATH_TO_EYES_RESULTS_NAME = "Applitools TestResults Path"
METADATA_EYES_TEST_RESULTS_URL_NAME = "Applitools Test Results Url"
EYES_TEST_JSON_NAME = "EyesTestResults"

T = TypeVar("T")  # Type variable for generic return types


def with_retry(max_retries: int = 3, delay: float = 0.5) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, bool]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Union[T, bool]:
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            return False

        return wrapper

    return decorator


class EyesResultsProcessor:
    """Handles the processing of Eyes test results for Robot Framework."""

    @staticmethod
    def process_results(result):
        # type: (Union[Result, TestSuite]) -> bool
        try:
            suite = result.suite if hasattr(result, "suite") else result
            return EyesResultsProcessor._process_suite_with_retry(suite)
        except Exception:
            return False

    @staticmethod
    @with_retry(max_retries=3, delay=0.5)
    def _process_suite_with_retry(suite):
        # type: (TestSuite) -> bool
        return EyesResultsProcessor._process_suite(suite)

    @staticmethod
    def _process_suite(suite):
        # type: (TestSuite) -> bool
        # Process child suites first
        sub_suite_changed = [
            EyesResultsProcessor._process_suite(s) for s in suite.suites
        ]

        # Check if this suite has Eyes test results metadata
        if suite.metadata.get(METADATA_PATH_TO_EYES_RESULTS_NAME):
            try:
                mgr = SuitePostProcessManager(suite)
                mgr.import_suite_data()
                mgr.process_suite()
                return True
            except Exception:
                # Continue processing other suites even if this one fails
                return any(sub_suite_changed)

        # Return True if any child suite was changed
        return any(sub_suite_changed)


# For backward compatibility
def process_results(result):
    # type: (Union[Result, TestSuite]) -> bool
    return EyesResultsProcessor.process_results(result)


# For backward compatibility
def propagate_test_results(suite):
    # type: (TestSuite) -> bool
    return EyesResultsProcessor._process_suite(suite)


def save_suites(path_to_test_results, suites):
    # type: (Text, dict[list[dict]]) -> None
    results = json.dumps(suites)
    with open(path_to_test_results, "w") as f:
        f.write(results)


def restore_suite(path_to_test_results):
    # type: (Text) -> dict[list[dict]]
    with open(path_to_test_results, "r") as f:
        return json.load(f)


def add_message_to_keyword(keyword, message):
    """
    Try different methods to add a message to a keyword based on Robot Framework version.

    Args:
        keyword: The Robot Framework keyword to add the message to
        message: The message text to add

    Returns:
        bool: True if the message was added successfully, False otherwise
    """
    methods = [
        # Method 1: Modern Robot Framework (>= 4.0)
        lambda: keyword.body.create_message(
            message=message,
            timestamp=format_timestamp(),
        ),
        # Method 2: Older Robot Framework with timestamp
        lambda: keyword.messages.create(
            message=message,
            timestamp=format_timestamp(),
        ),
        # Method 3: Last resort - without timestamp
        lambda: keyword.messages.create(
            message=message,
        ),
    ]

    for i, method in enumerate(methods):
        try:
            method()
            return True
        except Exception as e:
            robot_logger.debug(f"Message method {i+1} failed: {str(e)}")
            continue

    robot_logger.debug(f"Failed to add message '{message}' to keyword")
    return False


class SuitePostProcessManager(object):
    """Update Suite with data from json saved by `EyesToRobotTestResultsManager`"""

    def __init__(self, robot_suite):
        # type: (TestSuite) -> None
        self.robot_test_suite = robot_suite
        self.current_suite = None  # type: Optional[list[dict]]

    def import_suite_data(self):
        # type: () -> None
        """
        Import test results data from the file specified in suite metadata.

        Raises:
            KeyError: If no metadata key is found or suite name is not in results
            FileNotFoundError: If the test results file doesn't exist
        """
        path_to_test_results = self.robot_test_suite.metadata.get(
            METADATA_PATH_TO_EYES_RESULTS_NAME
        )

        if path_to_test_results is None:
            raise KeyError(
                f"No `{METADATA_PATH_TO_EYES_RESULTS_NAME}` found in metadata"
            )

        if not os.path.exists(path_to_test_results):
            raise FileNotFoundError(f"File `{path_to_test_results}` not found")

        suites_results_data = restore_suite(path_to_test_results)
        if self.robot_test_suite.name not in suites_results_data:
            raise KeyError("Suite name isn't found in results data")

        self.current_suite = suites_results_data[self.robot_test_suite.name]

        # Remove the metadata entry to avoid reprocessing
        self.robot_test_suite.metadata.pop(METADATA_PATH_TO_EYES_RESULTS_NAME)

    def process_suite(self):
        # type: () -> None
        if not self.current_suite:
            robot_logger.debug(
                "No tests found. Skip updating of test results of {}".format(
                    self.robot_test_suite
                )
            )
            return

        # Create lookup dict for test names -> (status, steps)
        robot_test_name_to_status = {
            t["test_name"]: (t["test_status"], t["steps"]) for t in self.current_suite
        }

        # Process each test in the suite
        for robot_test in self.robot_test_suite.tests:
            if robot_test.name not in robot_test_name_to_status:
                continue  # skip non-eyes tests

            # Update test status based on Eyes results
            robot_test_status, steps_info = robot_test_name_to_status[robot_test.name]
            robot_test.status = robot_test_status

            # Get all check keywords in the test
            check_keywords = all_check_keywords_recursively(robot_test)

            # Process each check keyword and corresponding step info
            self._process_check_keywords(check_keywords, steps_info)

        # Add the test results URL to suite metadata
        if self.current_suite:
            self.robot_test_suite.metadata[
                METADATA_EYES_TEST_RESULTS_URL_NAME
            ] = self.current_suite[0]["test_results_url"]

    def _process_check_keywords(self, check_keywords, steps_info):
        # type: (List[Keyword], List[dict]) -> None
        for check_keyword, step_info in zip(check_keywords, steps_info):
            # Update status based on the test results
            if step_info["is_different"]:
                self._propagate_status(check_keyword, "FAIL")
            else:
                check_keyword.status = "PASS"

            # Add the result URL as a message
            add_message_to_keyword(
                check_keyword, f"Check result url: {step_info['url']}"
            )

    @staticmethod
    def _propagate_status(keyword, status):
        # type: (Keyword, str) -> None
        call_chain = keyword
        while isinstance(call_chain, Keyword):
            call_chain.status = status
            call_chain = call_chain.parent


class EyesToRobotTestResultsManager(object):
    """
    Collects test results from Eyes, maps them to Robot Framework tests,
    and saves them to a JSON file. The path to the file is stored in Suite metadata.
    """

    def __init__(self, configure):
        # type: (Optional[RobotConfiguration]) -> None
        self.configure = configure

        # Early return if test results propagation is disabled
        if not self.configure or not self.configure.propagate_eyes_test_results:
            self.enabled = False
            return

        self.enabled = True
        self.test_id_to_suite = {}  # type: dict[Text, TestSuite]

        # Create a temporary directory for test results
        output_dir = tempfile.mkdtemp()
        self.path_to_test_results = os.path.join(
            output_dir, f"{EYES_TEST_JSON_NAME}-{uuid.uuid4().hex}.json"
        )
        robot_logger.debug(
            f"Test results will be saved to: {self.path_to_test_results}"
        )

    def register_robot_suite_started(self, data, result):
        # type: (TestSuite, TestSuite) -> None
        if not self.enabled:
            return
        # Store the path to test results in suite metadata
        result.metadata[METADATA_PATH_TO_EYES_RESULTS_NAME] = self.path_to_test_results
        robot_logger.debug(f"Registered suite start: {result.name}")

    def register_robot_test_started(self, data, result):
        # type: (TestSuite, TestSuite) -> None
        if not self.enabled:
            return

        # Generate a unique ID for this test
        self.configure.user_test_id = str(uuid.uuid4())
        robot_logger.debug(
            f"Registered test start: {result.name} with ID {self.configure.user_test_id}"
        )

    def register_robot_test_ended(self, data, result):
        # type: (TestSuite, TestSuite) -> None
        if not self.enabled:
            return

        # Map the test ID to the result
        self.test_id_to_suite[self.configure.user_test_id] = result
        robot_logger.debug(f"Registered test end: {result.name}")
        self.configure.user_test_id = None

    def register_eyes_test_results_on_close(self, test_results_summary):
        # type: (TestResultsSummary) -> None
        if not self.enabled:
            return

        robot_logger.debug("Processing Eyes test results on close")
        suites = defaultdict(list)

        # Process each test result and map it to the corresponding Robot test
        for test_results in self._process_test_results(test_results_summary):
            # Skip if we don't have a mapping for this test ID
            if test_results.user_test_id not in self.test_id_to_suite:
                robot_logger.debug(
                    f"No mapping found for test ID: {test_results.user_test_id}"
                )
                continue

            robot_test = self.test_id_to_suite[test_results.user_test_id]
            robot_test_name = robot_test.name
            robot_test_suite_name = robot_test.parent.name

            # Create a test result entry
            test_entry = {
                "test_name": robot_test_name,
                "test_status": EYES_STATUS_TO_ROBOT_STATUS[test_results.status],
                "test_results_url": test_results.url,
                "steps": [
                    {
                        "is_different": step.is_different,
                        "url": step.app_urls.step,
                    }
                    for step in test_results.steps_info
                ],
            }

            # Add to the appropriate suite
            suites[robot_test_suite_name].append(test_entry)
            robot_logger.debug(
                f"Added test result for '{robot_test_name}' in suite '{robot_test_suite_name}'"
            )

        # Save the results to the JSON file
        save_suites(self.path_to_test_results, suites)
        robot_logger.debug(f"Saved test results to: {self.path_to_test_results}")

    @staticmethod
    def _process_test_results(test_results_summary):
        # type: (TestResultsSummary) -> Generator[TestResults]
        """
        Process a test results summary to yield individual test results.

        For tests with multiple results, failed or unresolved results take precedence.
        If all results pass, the first result is used.
        """
        test_id_to_test_results = defaultdict(list)  # type: dict[list[TestResults]]

        for test_result_container in test_results_summary:
            test_id = test_result_container.user_test_id
            test_id_to_test_results[test_id].append(test_result_container.test_results)

        # Process each test's results
        for test_results_list in test_id_to_test_results.values():
            # First look for any failed or unresolved results
            for test_result in test_results_list:
                if test_result.status in [
                    TestResultsStatus.Failed,
                    TestResultsStatus.Unresolved,
                ]:
                    # If we find a failure, use it and stop processing this test
                    yield test_result
                    break
            else:
                # If no failures were found, use the first result
                yield test_results_list[0]


def all_check_keywords_recursively(test_or_kw):
    check_keywords = []
    for kw in test_or_kw.body:
        if isinstance(kw, Keyword):
            # Check if this is an Eyes check keyword
            if kw.libname == "EyesLibrary" and kw.kwname in CHECK_KEYWORDS_LIST:
                check_keywords.append(kw)
            else:
                # Otherwise, recursively search in this keyword
                check_keywords.extend(all_check_keywords_recursively(kw))
    return check_keywords
