from reporter.parser import parse_xml_report
from reporter.sender import send_report_to_lark, build_lark_message
from reporter.runner import run_maestro_command
from unittest.mock import patch, MagicMock
import unittest
import os


class TestMaestroReporter(unittest.TestCase):
    def setUp(self):
        # ensure the report.xml file always exists in the tests directory
        self.test_dir = os.path.dirname(__file__)
        self.report_file = os.path.join(self.test_dir, "report.xml")

    @patch("reporter.sender.requests.post")
    def test_e2e_runner_and_parser(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        parser = parse_xml_report(self.report_file)
        report = send_report_to_lark(
            summary=parser,
            title="Maestro Reporter Test",
            color_template="Green",
            webhook_url="",
        )
        self.assertFalse(report)
        self.assertEqual(mock_post.call_count, 0)

    def test_parser_report(self):
        parser = parse_xml_report(self.report_file)
        self.assertIsNotNone(parser)
        self.assertEqual(parser.device, "RRCWC060B0T")
        self.assertEqual(parser.duration, "5.97")
        self.assertEqual(parser.overall_status, "✅ Passed")

    def test_fake_command_maestro(self):
        fake_command = os.path.join(self.test_dir, "fake_maestro_flow.sh")
        self.assertTrue(os.path.exists(fake_command))
        result = run_maestro_command(fake_command, cwd=self.test_dir)
        # expected result is not None because the fake command would return a pathfile
        self.assertIsNotNone(result)

    def test_build_lark_message(self):
        summary = parse_xml_report(self.report_file)
        message = build_lark_message(
            summary=summary, title="Maestro Reporter Test", color_template="Green"
        )
        self.assertIsInstance(message, dict)
        self.assertEqual(message["msg_type"], "interactive")
        self.assertEqual(
            message["card"]["header"]["title"]["content"], "Maestro Reporter Test"
        )
        self.assertEqual(message["card"]["header"]["template"], "green")


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
