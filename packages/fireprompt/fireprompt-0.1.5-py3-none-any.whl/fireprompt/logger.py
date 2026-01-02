# fireprompt/logger.py
# SPDX-License-Identifier: MIT

# imports
import logging


# global debug mode state
_debug_mode = False

# track our loggers
_fireprompt_loggers = set()


class Logger:

    @staticmethod
    def get(name: str = "fireprompt"):
        """Get Logger instance."""
        ref = logging.getLogger(name)
        _fireprompt_loggers.add(name)

        if not ref.handlers:
            handler = logging.StreamHandler()

            # set formatter
            handler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s",
                    datefmt="%H:%M:%S"
                )
            )

            ref.addHandler(handler)
            ref.setLevel(logging.DEBUG if _debug_mode else logging.WARNING)

        return ref


def set_debug_mode(enabled: bool) -> None:
    """Set debug mode."""
    global _debug_mode
    _debug_mode = enabled

    for name in _fireprompt_loggers:
        logger = logging.getLogger(name)
        logger.setLevel(
            logging.DEBUG if enabled else logging.WARNING
        )
