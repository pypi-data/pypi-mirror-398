# Common test class with miscellaneous utilities and fixtures
import contextlib
import logging
import os
import shutil
import time
from pathlib import Path
from re import Pattern

import pytest
from _pytest.fixtures import FixtureRequest
from pathvalidate import sanitize_filename


@pytest.mark.usefixtures("logs")
class TestHelper:
    @property
    def output_folder(self) -> Path:
        """
        Output folder for the whole project (defaults to "<root folder>/out/tests").
        """

        return self.root_folder / "out" / "tests"

    @property
    def test_folder(self) -> Path:
        """
        Test folder for the current test (defaults to "<output folder>/__running__/<worker>/<test name>").
        """

        return self.output_folder / "__running__" / self.worker / self.test_name.replace("/", "_")

    @property
    def test_logs(self) -> Path:
        """
        Path to the current test logs file (i.e. pytest.log in the test folder)
        """

        return self.test_folder / "pytest.log"

    def check_logs(self, expected: str | Pattern[str] | list[str | Pattern[str]], timeout: int | None = None, check_order: bool = False):
        """
        Verify if expected pattern(s) can be found in current test logs.

        expected: may be:
            - a string (simple "contains" check)
            - a Pattern object (line match with regular expression)
            - a list of both (all list items must match)

        If timeout is provided, loop until either the pattern(s) is/are found or the timeout expires.

        If check_order is True, patterns will be verified in specified order; order doesn't matter otherwise

        :param expected: Expected pattern(s) to find in logs
        :param timeout: Timeout in seconds (None for no timeout)
        :param check_order: If True, patterns must be found in specified order
        :raises AssertionError: If some pattern is not found (after timeout if specified, else immediately)
        """
        retry = True
        init_time = time.time()
        to_check = expected if isinstance(expected, list) else [expected]

        # Iterate until timeout expires (if any)
        while retry:
            try:
                # Get logs content
                with self.test_logs.open("r", encoding="utf-8") as f:
                    lines = f.readlines()

                    # Verify all patterns are found in logs
                    start_index = 0
                    not_found_patterns = [p.pattern if isinstance(p, Pattern) else p for p in to_check]

                    # Iterate on patterns
                    for expected_pattern in to_check:
                        # Iterate on lines
                        for current_index, line_to_check in enumerate(lines[start_index:], start_index):
                            p_found = None
                            if isinstance(expected_pattern, Pattern):
                                # Check for regular expression (at least one line match)
                                if expected_pattern.search(line_to_check) is not None:
                                    p_found = expected_pattern.pattern
                            else:
                                # Simple string check
                                if expected_pattern in line_to_check:
                                    p_found = expected_pattern

                            # Pattern found (only first match)?
                            if p_found is not None and p_found in not_found_patterns:
                                not_found_patterns.remove(p_found)
                                if check_order:
                                    # Next pattern will have to be found after this line (patterns must respect input order)
                                    start_index = current_index + 1

                    # Verify we found all patterns
                    assert len(not_found_patterns) == 0, f"Missing patterns: {not_found_patterns}"

                    # If we get here: all expected patterns are found
                    retry = False
            except AssertionError as e:
                # Some pattern is still not found
                if timeout is None or (time.time() - init_time) >= timeout:
                    # No timeout, or timeout expired: raise assertion error
                    raise e
                else:
                    # Sleep a bit before checking logs again
                    time.sleep(0.5)

    @property
    def test_final_folder(self) -> Path:
        """
        Final test folder for the current test, once execution is complete (defaults to "<output folder>/<test name>")
        """

        return self.output_folder / self.test_name

    @property
    def test_module(self) -> str:
        """
        Test module, from which test file path is computed (defaults to 'tests') when building test name.

        If set to None or empty string, test file path will not be included in test name.
        """
        return "tests"

    @property
    def filter_test_prefixes(self) -> bool:
        """
        If True (default), "test_" and "Test" prefixes are removed from test name parts.
        """

        return True

    @property
    def test_name(self) -> str:
        """
        Test name, computed to be unique for each test, and to reflect test file path, class name, method name, and parameters (if any).

        Example: for a test method named "test_simple" in class "TestTheHelper" in file "tests/subtests/test_fromsubmodule.py",
                 the test name will be "subtests/test_fromsubmodule/TestTheHelper/test_simple".
                 If the test method is parameterized:
                    * parameters will be included in the method name (e.g. "test_simple[param1-param2]")
                    * parameters values are sanitized to be valid folder names
        """

        # Get pytest info, and grab info about test file path, class, and method (+ parameters if any)
        test_raw_path = Path(os.environ["PYTEST_CURRENT_TEST"].split(" ")[0])
        test_elements = test_raw_path.name.split("::")
        test_file_full_path = test_raw_path.parent / test_elements[0]

        # If test module is set, compute test file path relative to it
        if self.test_module:
            # Compute path relative to test module
            test_file_parts = list(test_file_full_path.parts)
            if self.test_module in test_file_parts:
                # Module found: compute test file path relative to it
                test_module_path = Path(*test_file_parts[0 : test_file_parts.index(self.test_module) + 1])
                test_file = test_file_full_path.relative_to(test_module_path)
            else:
                # Can't find test module: simply use test file name
                test_file = Path(test_file_full_path.name)

            # Name root if test file parts (without the ".py" extension)
            name_root = list((test_file.parent / test_file.name.replace(".py", "")).parts)
        else:
            # No name root (name will be only based on class name)
            name_root = []

        # Concatenate path to class + method names; also filter out "test_" and "Test" prefixes
        all_parts: list[str] = []
        for part in name_root + list(map(sanitize_filename, test_elements[1:])):
            part_to_keep = part
            if self.filter_test_prefixes and part_to_keep.startswith("test_"):
                part_to_keep = part_to_keep[5:]
            if self.filter_test_prefixes and part_to_keep.startswith("Test"):
                part_to_keep = part_to_keep[4:]
            if part_to_keep:
                all_parts.append(part_to_keep)
        return "/".join(all_parts)

    @property
    def worker(self) -> str:
        """
        Worker name in parallelized tests: master for non-parallelized tests, or e.g. "gw0", "gw1", etc. for parallelized tests.
        """

        return os.environ.get("PYTEST_XDIST_WORKER", "master")

    @property
    def worker_index(self) -> int:
        """
        Worker index as integer (0 for master or "gw0", 1 for "gw1", etc.).
        """

        worker = self.worker
        return int(worker[2:]) if worker.startswith("gw") else 0

    # Per-test logging management
    @pytest.fixture
    def logs(self, request: FixtureRequest):
        # Set root folder
        self.root_folder = request.config.rootpath.absolute().resolve()

        # Prepare test folder
        shutil.rmtree(self.test_folder, ignore_errors=True)
        shutil.rmtree(self.test_final_folder, ignore_errors=True)
        self.test_folder.mkdir(parents=True, exist_ok=False)

        # Install logging
        log_format = f"%(asctime)s.%(msecs)03d [{self.worker}/%(name)s] %(levelname)s %(message)s - %(filename)s:%(funcName)s:%(lineno)d"
        date_format = "%Y-%m-%d %H:%M:%S"
        test_file_handler = logging.FileHandler(filename=str(self.test_logs), mode="w", encoding="utf-8")
        test_file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logging.root.setLevel(logging.DEBUG)
        logging.root.addHandler(test_file_handler)

        logging.info("-----------------------------------------------------------------------------------")
        logging.info(f"    New test: {self.test_name}")
        logging.info("-----------------------------------------------------------------------------------")

        # Return to test
        yield

        # Flush logs
        logging.info("-----------------------------------------------------------------------------------")
        logging.info(f"    End of test: {self.test_name}")
        logging.info("-----------------------------------------------------------------------------------")
        test_file_handler.close()
        logging.root.removeHandler(test_file_handler)

        # Move folder
        shutil.move(self.test_folder, self.test_final_folder)
        with contextlib.suppress(OSError):
            # Tentatively remove worker folder if empty
            self.test_folder.parent.rmdir()
