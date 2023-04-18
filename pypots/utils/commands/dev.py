"""
CLI tools to help the development team build PyPOTS.
"""

# Created by Wenjie Du <wenjay.du@gmail.com>
# License: GLP-v3

import os
import shutil
from argparse import ArgumentParser, Namespace

from pypots.utils.commands import BaseCommand
from pypots.utils.logging import logger

IMPORT_ERROR_MESSAGE = (
    "`pypots-cli dev` command is for PyPOTS developers to run tests easily. "
    "Therefore, you need a complete PyPOTS development environment. However, you are missing some dependencies. "
    "Please refer to https://github.com/WenjieDu/PyPOTS/blob/main/environment-dev.yml for dependency details. "
)


def dev_command_factory(args: Namespace):
    return DevCommand(
        args.build,
        args.cleanup,
        args.run_tests,
        args.k,
        args.show_coverage,
        args.lint_code,
    )


class DevCommand(BaseCommand):
    """CLI tools helping develop PyPOTS. Easy the running of tests and code linting with Black and Flake8.

    Examples
    --------
    $ pypots-cli dev --run_tests
    $ pypots-cli dev --run_tests --show_coverage  # show code coverage
    $ pypots-cli dev --run_tests -k imputation  # only run tests cases of imputation models
    $ pypots-cli dev --lint_code  # use Black to reformat the code and apply Flake8 to lint code

    """

    @staticmethod
    def register_subcommand(parser: ArgumentParser):
        sub_parser = parser.add_parser(
            "dev", help="CLI tools helping develop PyPOTS code"
        )
        sub_parser.add_argument(
            "--build",
            dest="build",
            action="store_true",
            help="Build PyPOTS into a wheel and package the source code into a .tar.gz file for distribution",
        )
        sub_parser.add_argument(
            "--cleanup",
            dest="cleanup",
            action="store_true",
            help="Delete all caches and building files",
        )
        sub_parser.add_argument(
            "--run_tests",
            dest="run_tests",
            action="store_true",
            help="Run all test cases",
        )
        sub_parser.add_argument(
            "--show_coverage",
            dest="show_coverage",
            action="store_true",
            help="Show the code coverage report after running tests",
        )
        sub_parser.add_argument(
            "-k",
            type=str,
            default=None,
            help="The -k option of pytest. Description of -k option in pytest: "
            "only run tests which match the given substring expression. An expression is a python evaluatable "
            "expression where all names are substring-matched against test names and their parent classes. "
            "Example: -k 'test_method or test_other' matches all test functions and classes whose name contains "
            "'test_method' or 'test_other', while -k 'not test_method' matches those that don't contain "
            "'test_method' in their names. -k 'not test_method and not test_other' will eliminate the matches. "
            "Additionally keywords are matched to classes and functions containing extra names in their "
            "'extra_keyword_matches' set, as well as functions which have names assigned directly to them. The "
            "matching is case-insensitive.",
        )
        sub_parser.add_argument(
            "--lint_code",
            dest="lint_code",
            action="store_true",
            help="Run Black and Flake8 to lint code",
        )
        sub_parser.set_defaults(func=dev_command_factory)

    def __init__(
        self,
        build: bool,
        cleanup: bool,
        run_tests: bool,
        k: str,
        show_coverage: bool,
        lint_code: bool,
    ):
        self._build = build
        self._cleanup = cleanup
        self._run_tests = run_tests
        self._k = k
        self._show_coverage = show_coverage
        self._lint_code = lint_code

    def check_arguments(self):
        """Run some checks on the arguments to avoid error usages"""
        containing_docs = "docs" in os.listdir(".")
        containing_pypots = "pypots" in os.listdir(".")
        # if currently under dir 'docs', it should have sub-dir 'figs', and 'pypots' should be in the parent dir
        whether_under_dir_docs = containing_docs and containing_pypots
        # `pypots-cli dev` should only be run under dir 'docs'
        # because we probably will compile the doc and generate HTMLs with command `make`
        assert whether_under_dir_docs, (
            "Command `pypots-cli dev` can only be run under the root directory of project PyPOTS, "
            f"but you're running it under the path {os.getcwd()}. Please make a check."
        )

        if self._k is not None:
            assert self._run_tests, (
                "Argument `-k` should combine the use of `--run_tests`. "
                "Try `pypots-cli dev --run_tests -k your_pattern`"
            )

        if self._show_coverage:
            assert self._run_tests, (
                "Argument `--show_coverage` should combine the use of `--run_tests`. "
                "Try `pypots-cli dev --run_tests --show_coverage`"
            )

        if self._cleanup:
            assert not self._run_tests and not self._lint_code, (
                "Argument `--cleanup` should be used alone. "
                "Try `pypots-cli dev --cleanup`"
            )

    def run(self):
        """Execute the given command."""

        # check arguments first
        self.check_arguments()

        try:
            if self._cleanup:
                shutil.rmtree("build", ignore_errors=True)
                shutil.rmtree("dist", ignore_errors=True)
                shutil.rmtree("pypots.egg-info", ignore_errors=True)
            elif self._build:
                self.execute_command("python setup.py sdist bdist bdist_wheel")
            elif self._run_tests:
                pytest_command = f"pytest -k {self._k}" if self._k else "pytest"
                command_to_run_test = (
                    f"coverage run -m {pytest_command}"
                    if self._show_coverage
                    else pytest_command
                )
                logger.info(f"Executing '{command_to_run_test}'...")

                self.execute_command(command_to_run_test)
                if self._show_coverage:
                    self.execute_command("coverage report -m")
                    self.execute_command("rm -rf .coverage")

                self.execute_command("rm -rf .pytest_cache")

            elif self._lint_code:
                logger.info("Reformatting with Black...")
                self.execute_command("black .")
                logger.info("Linting with Flake8...")
                self.execute_command("flake8 .")

        except ImportError:
            raise ImportError(IMPORT_ERROR_MESSAGE)
        except Exception as e:
            raise RuntimeError(e)
