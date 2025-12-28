import os
import argparse
import sys
from .logger import get_logger
from .runner import run_maestro_command
from .parser import parse_xml_report
from .sender import send_report_to_lark
from dotenv import load_dotenv


load_dotenv()
log = get_logger("main")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Maestro tests with a custom reporter, parse the report and send it to Lark"
    )

    parser.add_argument("--command", "-c", type=str, help="Maestro command to run")
    parser.add_argument(
        "--report",
        "-r",
        type=str,
        default="report.xml",
        help="Path to Maestro report, by default it's `report.xml`",
    )
    parser.add_argument(
        "--webhook",
        "-w",
        type=str,
        help="Specify a webhook URL to send the report to Lark",
    )
    parser.add_argument(
        "--no-run",
        "-n",
        action="store_true",
        help="No need to run Maestro tests, just parse the report",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        help="Set a custom title for the interactive card Lark message",
    )
    parser.add_argument(
        "--color",
        "-ct",
        type=str,
        help="Set a custom color template for the interactive card Lark message",
    )

    args = parser.parse_args()
    report_path = args.report

    if not args.color:
        log.warning(
            "No color template provided, using default color template or you can set it with `--color` flag"
        )

    if not args.title:
        log.warning(
            "No title provided, using default title or you can set it with `--title` flag"
        )

    if not args.no_run:
        if not args.command:
            log.error("No Maestro command provided, use `--command` or `--no-run`")
            sys.exit(1)

        log.info(f"Running Maestro command: {args.command}")
        generated_report = run_maestro_command(args.command)

        if not generated_report:
            log.error("Failed to generate Maestro report")
            sys.exit(1)

        # use returned report path if it's available
        report_path = str(generated_report)

        if not os.path.exists(report_path):
            log.error(f"Maestro report file does not exists: {report_path}")
            sys.exit(1)
    else:
        log.info("--no-run flag is set, skipping Maestro tests")

        if not os.path.exists(report_path):
            log.error(f"Maestro report file does not exists: {report_path}")
            sys.exit(1)

    log.info(f"Parsing Maestro report file: {report_path}")
    parsed_report = parse_xml_report(report_path)
    if parsed_report is None:
        log.error("Failed to parse Maestro report")
        sys.exit(1)

    webhook_url = args.webhook or os.getenv("LARK_URL")
    if not webhook_url:
        log.error(
            "No webhook URL provided, use `--webhook` or set LARK_URL environment variable"
        )
        sys.exit(1)

    log.info("Sending Maestro report to Lark...")
    send_report_to_lark(
        parsed_report,
        title=args.title or "Maestro Testing Report",
        color_template=args.color or "Green",
        webhook_url=webhook_url,
    )
    log.info("Maestro report sent successfully")


if __name__ == "__main__":
    main()
