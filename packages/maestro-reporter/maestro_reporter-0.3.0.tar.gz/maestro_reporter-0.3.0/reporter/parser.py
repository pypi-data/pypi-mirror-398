import xml.etree.ElementTree as ET
from pathlib import Path
from .logger import get_logger
from .models import TestSuiteSummary


log = get_logger(__name__)


def _safe_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _set_default_status(status: str, has_failure: bool) -> str:
    """
    Normalize the default status based on the testcases status. The report
    may contain different status label, this function is to preserved relevant labes
    """
    if has_failure:
        # usually, the returned status from Junit may used "FAILED"
        # here, we returned that status as default "Failed"
        return "Failed"
    stats = (status or "").strip().lower()
    if not stats:
        return "Passed"
    return stats.title()


def _truncate_message(text: str, max_chars: int = 1000) -> str:
    """
    Function to truncated the failure message from the testsuite report,
    if more than maximum characters, then just display it as "...",
    so it can be more enrich during displayed in the Lark interactive message
    """
    if not text:
        return "-"
    text = text.strip()

    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def parse_xml_report(file_path: str) -> TestSuiteSummary:
    """
    Parses the Maestro report XML file and returns a `TestSuiteSummary` object

    :param file_path: path to the Maestro report XML file that you want to parse
    """
    file_path_location = Path(file_path)
    if not file_path_location.exists():
        log.error(f"Maestro report file does not exists: {file_path_location}")
        return None

    try:
        tree = ET.parse(file_path_location)
        root = tree.getroot()

        # always find the test suite summary based on the root element,
        # this approach is more robust rather than using the `testsuites` element
        test_suite = root.find(".//testsuite")
        if test_suite is None:
            log.error("Could not find test suite summary in the report")
            return None

        device = test_suite.get("device", "Unknown Device")
        total_tests = len(test_suite.findall("testcase"))
        failed_tests = int(test_suite.get("failures", 0))
        response_time = float(test_suite.get("time", 0))
        converted_response_time = f"{response_time / 60:.2f}"

        test_cases = []
        for test_case in test_suite.findall("testcase"):
            failure_element = test_case.find("failure")
            has_failure = failure_element is not None
            extract_status = test_case.get("status", "") or ""
            set_status = _set_default_status(
                status=extract_status, has_failure=has_failure
            )
            failure_msg = _truncate_message(
                failure_element.text if failure_element is not None else None,
                max_chars=1000,
            )
            safe_duration_time = _safe_float(
                value=test_case.get("time", 0.0), default=0.0
            )
            test_cases.append(
                {
                    "id": test_case.get("id", "Unknown ID"),
                    "name": test_case.get("name", "Unknown Name"),
                    "classname": test_case.get("classname", "Unknown Classname"),
                    "time": f"{safe_duration_time} secs",
                    "status": set_status,
                    "failure_message": failure_msg or "-",
                }
            )

        overall_status = "✅ Passed" if failed_tests == 0 else "❌ Failed"

        return TestSuiteSummary(
            device=device,
            total_tests=total_tests,
            failed_tests=failed_tests,
            duration=converted_response_time,
            overall_status=overall_status,
            test_cases=test_cases,
        )
    except ET.ParseError as e:
        log.error(f"Failed to parse XML report: {e}")
        return None
    except Exception as e:
        log.error(f"Uncaught exception while parsing XML report: {e}")
        return None
