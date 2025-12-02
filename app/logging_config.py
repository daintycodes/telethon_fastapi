import logging
import os


def configure_logging():
    """Configure application logging.

    Sets up a basic logging configuration that integrates with Uvicorn
    and writes logs at INFO level by default. Honors LOG_LEVEL env var.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Reduce verbosity of noisy libraries by default
    logging.getLogger("uvicorn.error").setLevel(getattr(logging, log_level, logging.INFO))
    logging.getLogger("uvicorn.access").setLevel(getattr(logging, log_level, logging.INFO))
