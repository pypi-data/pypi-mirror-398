import click
from schemathesis import cli

group = cli.add_group("Coverage options")
group.add_option(
    "--coverage-format",
    help="Output format for coverage reports",
    type=click.Choice(["text", "html"]),
    default="html",
    metavar="FORMAT",
    envvar="SCHEMATHESIS_COVERAGE_FORMAT",
)
group.add_option(
    "--coverage-report-path",
    help="File path for the API coverage report",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        writable=True,
        path_type=str,
    ),
    envvar="SCHEMATHESIS_COVERAGE_REPORT_PATH",
)
group.add_option(
    "--coverage-no-report",
    help="Do not generate coverage report",
    is_flag=True,
    default=False,
    envvar="SCHEMATHESIS_COVERAGE_NO_REPORT",
)
group.add_option(
    "--coverage-show-missing",
    help="Show items with no coverage",
    type=click.Choice(["parameters"]),
    default=None,
    metavar="",
    envvar="SCHEMATHESIS_COVERAGE_SHOW_MISSING",
)
group.add_option(
    "--coverage-skip-covered",
    help="Skip operations with 100% coverage",
    is_flag=True,
    default=False,
    envvar="SCHEMATHESIS_COVERAGE_SKIP_COVERED",
)
group.add_option(
    "--coverage-skip-empty",
    help="Skip operations without any collected data",
    is_flag=True,
    default=False,
    envvar="SCHEMATHESIS_COVERAGE_SKIP_EMPTY",
)
