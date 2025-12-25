from __future__ import annotations

import pytest


class PytestIntegrational:
    """
    Handle "integrational" tests.

    Add hooks to the main `conftest.py`:

        def pytest_addoption(parser):
            PytestIntegrational.pytest_addoption(parser)

        def pytest_configure(config):
            PytestIntegrational.pytest_configure(config)

        def pytest_collection_modifyitems(config, items) -> None:
            PytestIntegrational.pytest_collection_modifyitems(config, items)

    (this should probably be wrapped as a pytest plugin later)

    Mark a test as integrational:

        @pytest.mark.integrational()

    Run integrational tests:

        poetry run hydpytest --log-cli-level=1 --integrational -v -s

    https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option

    Requires a fixture `_allow_external` to exist.
    """

    _MARK_ALLOW_EXTERNAL = pytest.mark.usefixtures("_allow_external")
    _MARK_SKIP_INTEGRATIONAL = pytest.mark.skip(reason="need `--integrational` option to run")

    @staticmethod
    def pytest_addoption(parser):
        parser.addoption(
            "--integrational", action="store_true", default=False, help="run integrational (networked) tests"
        )

    @staticmethod
    def pytest_configure(config):
        config.addinivalue_line("markers", "integrational: mark test as requiring external network")

    @classmethod
    def pytest_collection_modifyitems(cls, config, items) -> None:
        integrational = config.getoption("--integrational")
        for item in items:
            if "integrational" in item.keywords:
                # Either skip the test or allow external requests.
                if integrational:
                    item.add_marker(cls._MARK_ALLOW_EXTERNAL)
                    # Apparently marker at this point is not enough.
                    item.fixturenames.append("_allow_external")
                else:
                    item.add_marker(cls._MARK_SKIP_INTEGRATIONAL)
