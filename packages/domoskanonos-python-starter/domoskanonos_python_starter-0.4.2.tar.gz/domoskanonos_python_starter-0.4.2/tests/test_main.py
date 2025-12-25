import pytest

from project.main import main


def test_main_execution() -> None:
    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised {e} unexpectedly!")


def test_placeholder() -> None:
    assert True
