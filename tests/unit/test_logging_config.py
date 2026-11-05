import logging

from iac_converter.logging_config import configure_logging


def test_default_logging_uses_warning_level() -> None:
    configure_logging()

    assert logging.getLogger().level == logging.WARNING


def test_verbose_logging_uses_debug_level() -> None:
    configure_logging(verbose=True)

    assert logging.getLogger().level == logging.DEBUG


def test_quiet_logging_uses_error_level() -> None:
    configure_logging(quiet=True)

    assert logging.getLogger().level == logging.ERROR


def test_quiet_takes_precedence_over_verbose() -> None:
    configure_logging(verbose=True, quiet=True)

    assert logging.getLogger().level == logging.ERROR
