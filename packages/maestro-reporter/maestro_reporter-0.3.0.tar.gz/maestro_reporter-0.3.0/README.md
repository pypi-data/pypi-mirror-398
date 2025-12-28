## py-maestro-reporter

![badge](https://gitlab.com/ryaneatfood/py-maestro-reporter/badges/master/pipeline.svg) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/maestro-reporter) ![coverage](https://gitlab.com/ryaneatfood/py-maestro-reporter/badges/master/coverage.svg)


Customized tool to run Maestro tests, parse Maestro report file and send the parsed report to Lark respective group. This tool allows you to run Maestro tests seamlessly by providing built-in methods to run the tests and also CLI arguments to directly run the without having to write any code

### Prerequisites

- Python 3.10 or above
- [Maestro framework](https://docs.maestro.dev/getting-started/installing-maestro) installed on your system (version 2.0.0 or above)
- Device/emulator with the app under test installed
- Lark webhook URL

### Installation

For the installation, you can either install the package from PyPI or from source. If you'd like to install from PyPI, you can install it with:

```bash
pip install maestro-reporter
```

Or, using uv:

```bash
uv pip install maestro-reporter
```

Or, if you'd prefer to install from source, you'll need to clone this repository and install it in editable mode:

```bash
pip install -e .
```

### Usage

**Using as a CLI argument**

As you can see, this package also provides a CLI tool to run Maestro tests and parse the report immediately. To do this, all you need to do is, ensure you have Maestro installed on your device, example flows which is going to be tested, physical device or emulator and Webhook URL from Lark. Once you have all of these, you can run with CLI arguments such as:

```bash
python -m reporter -c "maestro test examples/facebook-sign-up-flow.yaml --format junit --output tests/report.xml" -r "tests/report.xml" -w "https://webhook.url.com"
```

Or, if you only want to run and parse the report without testing, you can use `--no-run` flag


```bash
python -m reporter --no-run -r "tests/report.xml" -w "https://webhook.url.com"
```

> You can also overrides the Webhook URL by setting the `LARK_URL` environment variable in your `.env` file

**Using the reporter package**

Otherwise, if you'd like to run the tests without using the CLI arguments and you need to run the tests with the `reporter` package, you can follow the example below (this will test the Facebook sign up flow):

```python
import os
from dotenv import load_dotenv
from reporter import parse_xml_report, send_report_to_lark, run_maestro_command


load_dotenv()


command = "maestro test examples/facebook-sign-up-flow.yaml --format junit --output tests/report.xml"
run_maestro_command(command=command, cwd="tests")
parsed_result = parse_xml_report(file_path="report.xml")
report = send_report_to_lark(
    summary=parsed_result,
    title="Maestro Reporter Test",
    color_template="Green",
    webhook_url=os.getenv("LARK_URL"),
)
```

The parameters of `color_template` and `title` are mandatory, if you don't provide them, the default values will be used

All successful tests (from execute the Maestro command -> parse the report -> send the report to Lark) will be displayed in the log stream handler, for example:

```
27-11-2025 : 10:51:46 : main : [WARNING] : No color template provided, using default color template or you can set it with `--color` flag
27-11-2025 : 10:51:46 : main : [WARNING] : No title provided, using default title or you can set it with `--title` flag
27-11-2025 : 10:51:46 : main : [INFO] : --no-run flag is set, skipping Maestro tests
27-11-2025 : 10:51:46 : main : [INFO] : Parsing Maestro report file: tests/report.xml
27-11-2025 : 10:51:46 : main : [INFO] : Sending Maestro report to Lark...
27-11-2025 : 10:51:46 : reporter.sender : [INFO] : Lark message sent successfully
27-11-2025 : 10:51:46 : main : [INFO] : Maestro report sent successfully
```

Once the report is sent successfully, you should be able to see the interactive card message in your Lark group like the following image

![Lark Interactive Card Message](https://gitlab.com/ryaneatfood/py-maestro-reporter/-/raw/master/images/maestro-result.png)

### CLI arguments

List of available CLI arguments that you can use with this package:

| arguments | description |
| --- | --- |
| `-h` / `--help` | show this help message and exit |
| `-c` / `--command` | Maestro command to run |
| `-r` / `--report` | Path to Maestro report, by default it's `report.xml` but you can configure it by yourself |
| `-w` / `--webhook` | Specify a webhook URL to send the report to Lark |
| `-n` / `--no-run` | No need to run Maestro tests, just parse the report and send the result to Lark |
| `-t` / `--title` | Set a custom title for the interactive card Lark message |
| `-ct` / `--color` | Set a custom color template for the interactive card Lark message |

**Notes**

- At the moment, this package only supports the parsing of the `junit` format as follows for the Maestro report
- In addition, the webhook integration currently only supports for Lark. At the meantime, we're working on adding more integrations with other platforms
- The interactive card message is built using the `msg_actioncard` message type, which is currently only supported by Lark. Any customizable message types will be added in the future release

**Further references**

- [Generate report with Maestro](https://docs.maestro.dev/cli/test-suites-and-reports)
- [Setup Lark Webhook URL in Lark group](https://open.larksuite.com/document/client-docs/bot-v3/add-custom-bot)