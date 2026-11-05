from __future__ import annotations

import logging
import sys


def configure_logging(
    *,
    verbose: bool = False,
    quiet: bool = False,
) -> None:
    """Configure application logging."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )
