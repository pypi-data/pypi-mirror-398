from __future__ import annotations

import argparse
import logging
import logging.config
import os
import sys
from io import TextIOWrapper
from typing import cast

from elevenlabs import ElevenLabs
from elevenlabs.core import ApiError

from pyscribe import __version__
from pyscribe.errors import FileTooLargeError
from pyscribe.transcriber import transcribe
from pyscribe.utils import get_keyring_api_key, set_keyring_api_key

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    "invalid_api_key": "Invalid API Key. Check your --key argument or ELEVENLABS_API_KEY env var.",
    "quota_exceeded": "Quota Exceeded. You have run out of credits. Upgrade at elevenlabs.io.",
    "only_for_creator": "Only For Creator. You are trying to use a feature locked to a higher tier.",
    "too_many_concurrent_requests": (
        "Too Many Concurrent Requests. You have exceeded the concurrency limit for your subscription."
    ),
    "system_busy": "System Busy. The ElevenLabs servers are under heavy load. Try again later.",
}


class Args(argparse.Namespace):
    source: str
    key: str | None
    lang: str | None
    full: bool
    verbose: bool


def parse_args() -> Args:
    parser = argparse.ArgumentParser(
        prog="pyscribe",
        description="Audio transcriber powered by the ElevenLabs Scribe AI model.",
    )
    parser.add_argument(
        "source",
        help="File path or HTTPS URL to transcribe",
    )
    parser.add_argument(
        "--key",
        help="ElevenLabs API key",
        default=os.getenv("ELEVENLABS_API_KEY"),
    )
    parser.add_argument(
        "--lang",
        help="ISO-639-1 or ISO-639-3 language code for better performance",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="insert audio event tags like [laughter]",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable debug logs",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(namespace=Args())


def setup_logging(verbose: bool) -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(message)s",
                },
            },
            "handlers": {
                "stderr": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "stream": sys.stderr,
                },
            },
            "loggers": {
                "pyscribe": {
                    "level": logging.DEBUG if verbose else logging.INFO,
                    "handlers": ["stderr"],
                    "propagate": False,
                }
            },
            "root": {
                "level": logging.WARNING,
                "handlers": ["stderr"],
            },
        },
    )


def handle_error(error: ApiError) -> None:
    status_code = error.status_code or 500
    if status_code == 422:
        logger.error("Unprocessable Entity. Server rejected the request. Try another format?")
    else:
        body = str(cast(str, error.body))
        for reason, message in ERROR_MESSAGES.items():
            if reason in body:
                logger.error(message)
                break
        else:
            logger.exception("Unexpected error.")


def main() -> None:
    if sys.platform == "win32" and isinstance(sys.stdout, TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    logger.debug("Parsed arguments: %s", args)
    setup_logging(args.verbose)

    api_key = args.key or get_keyring_api_key()

    if not api_key:
        logger.critical("API key is required. Use --key parameter or set ELEVENLABS_API_KEY env var.")
        sys.exit(1)

    client = ElevenLabs(api_key=api_key)
    try:
        lyrics = transcribe(client, args.source, args.full, args.lang)
    except ApiError as e:
        handle_error(e)
        sys.exit(1)
    except (FileNotFoundError, FileTooLargeError) as e:
        logger.critical(e)
        sys.exit(1)

    if lyrics.strip():
        print(lyrics)
    else:
        logger.warning("Server returned an empty transcript.")

    if args.key:
        set_keyring_api_key(api_key)


if __name__ == "__main__":
    main()
