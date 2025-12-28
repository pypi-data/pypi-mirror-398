from dataclasses import dataclass
from typing import List


@dataclass
class TestCase:
    id: str
    name: str
    classname: str
    status: str
    time_seconds: float
    failure_message: str


@dataclass
class TestSuiteSummary:
    device: str
    total_tests: int
    failed_tests: int
    duration: float
    overall_status: str
    test_cases: List[TestCase]
