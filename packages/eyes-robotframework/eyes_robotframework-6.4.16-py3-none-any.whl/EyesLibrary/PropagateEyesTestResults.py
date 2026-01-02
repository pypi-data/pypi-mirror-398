from robot.api import SuiteVisitor
from robot.model import TestSuite
from robot.result.executionresult import Result

from .test_results_manager import process_results


class PropagateEyesTestResults(SuiteVisitor):
    """Robot rebot SuiteVisitor that propagates Eyes test results to Robot results"""

    def start_suite(self, suite):
        # type: (TestSuite|Result) -> None
        process_results(suite)
