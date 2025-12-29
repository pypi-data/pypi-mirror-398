import pytest

TEST_GROUPS = {"all", "content_unittesting"}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--blends-test-group",
        action="store",
        metavar="BLENDS_TEST_GROUP",
    )


def pytest_runtest_setup(item: pytest.Module) -> None:
    blends_test_group = item.config.getoption("--blends-test-group")

    if not blends_test_group:
        try:
            marker = next(x for x in item.iter_markers(name="blends_test_group"))
        except StopIteration as exc:
            exc_log = "blends-test-group not specified"
            raise ValueError(exc_log) from exc
        blends_test_group = marker.args[0]

    if blends_test_group != "all" and blends_test_group not in TEST_GROUPS:
        exc_log = f"blends-test-group must be one of: {TEST_GROUPS}, or all"
        raise ValueError(exc_log)

    runnable_groups = {mark.args[0] for mark in item.iter_markers(name="blends_test_group")}

    if not runnable_groups or runnable_groups - TEST_GROUPS:
        exc_log = f"blends-test-group must be one of: {TEST_GROUPS}"
        raise ValueError(exc_log)

    if blends_test_group != "all" and blends_test_group not in runnable_groups:
        pytest.skip(f"Requires blends test group in: {runnable_groups}")
