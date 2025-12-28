import os
import requests
from typing import Any
from .logger import get_logger
from .models import TestSuiteSummary


log = get_logger(__name__)

VALID_LARK_COLORS = [
    "blue",
    "wathet",
    "turquoise",
    "green",
    "yellow",
    "orange",
    "red",
    "carmine",
    "violet",
    "purple",
    "indigo",
    "grey",
]


def _validate_lark_color(color: str) -> str:
    """
    Validates if the provided color is a valid Lark color template,
    normalized color is returned and displayed as `green` if invalid color provided

    :param color: color template to validate
    """

    if not color:
        return "green"

    normalized_color = color.strip().lower()
    if normalized_color not in VALID_LARK_COLORS:
        raise ValueError(f"Invalid Lark color template: {color}")

    return normalized_color


def build_lark_message(
    summary: TestSuiteSummary, title: str, color_template: str
) -> dict[str, Any]:
    """
    Builds an interactive card message for Lark with customized title and color template

    :param summmary: TestSuiteSummary object
    :param title: custom title for the Lark interactive card
    :param color_template: color template for the Lark interactive card
    """
    _summary = (
        f"Device: {summary.device}\n"
        f"Total Tests: {summary.total_tests}\n"
        f"Failed Tests: {summary.failed_tests}\n"
        f"Duration: {summary.duration} mins\n"
        f"Overall Status: {summary.overall_status}"
    )

    validated_color = _validate_lark_color(color=color_template)

    msg_actioncard = {
        "msg_type": "interactive",
        "update_multi": False,
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title,
                },
                "template": validated_color,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"{_summary}",
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**Test Cases Details:**\n"
                        + "\n".join(
                            f"- **{case['name']}**: {case['status']}\n"
                            f"  Failure Message: **{case['failure_message'] if case['status'] == 'Failed' else '-'}**\n"
                            f"  Execution Testing Time: {case['time']}"
                            for case in summary.test_cases
                        ),
                    },
                },
            ],
        },
    }

    return msg_actioncard


def send_report_to_lark(
    summary: TestSuiteSummary,
    title: str,
    color_template: str,
    webhook_url: str,
    timeout: int = 10,
) -> bool:
    """
    Sends the test report to Lark using the provided Webhook URL, all parameters are required,
    if `color_template` or `title` is not provided, default values will apply

    :param summary: summary of the test suite, this is the output from `parse_xml_report` function
    :param title: title of the interactive card in Lark
    :param color_template: color template for the interactive card in Lark
    :param webhook_url: webhook URL to send the report to Lark group
    :param timeout: timeout for the request to Lark, by default it's 10 seconds
    """
    if not webhook_url:
        log.error(
            "No URL Lark webhook provided, please set LARK_URL environment variable"
        )
        return False

    payload = build_lark_message(
        summary=summary, title=title, color_template=color_template
    )
    try:
        response = requests.post(url=webhook_url, json=payload, timeout=timeout)
        if response.status_code == 200:
            log.info("Lark message sent successfully")
            return True
        else:
            log.error(
                f"Failed to send Lark message with status code: {response.status_code}"
            )
            return False
    except requests.exceptions.RequestException as e:
        log.error(f"Uncaught exception while sending Lark message: {e}")
        return False
