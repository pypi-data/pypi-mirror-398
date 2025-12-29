from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import keyring

from pyscribe.errors import FileTooLargeError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import BinaryIO, TypedDict

    class ScribeArgs(TypedDict, total=False):
        model_id: str
        tag_audio_events: bool
        language_code: str
        cloud_storage_url: str


logger = logging.getLogger(__name__)


KEYRING_SERVICE_NAME = "pyscribe"
KEYRING_USERNAME = "api_key"

MAX_FILE_SIZE_BYTES = 3e9
MAX_FILE_SIZE_HUMAN = f"{MAX_FILE_SIZE_BYTES / 1e9:g} GB"


def get_keyring_api_key() -> str | None:
    logger.debug("Getting API key from keyring")
    return keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME)


def set_keyring_api_key(api_key: str) -> None:
    logger.debug("Saving API key to keyring")
    keyring.set_password(KEYRING_SERVICE_NAME, KEYRING_USERNAME, api_key)


def disambiguate_source(source: str | Path) -> str | Path:
    if isinstance(source, str):
        if source.startswith("http://"):
            logger.info("HTTP URLs are not supported. Converting the HTTP URL to HTTPS.")
            source = f"https://{source[7:]}"

        if source.startswith("https://"):
            return source

    file = Path(source)
    logger.debug("Source is not a URL. Validating file '%s'.", file)

    if not file.is_file():
        raise FileNotFoundError(f"File '{file}' not found.")

    file_size = file.stat().st_size
    logger.debug("File size = %d bytes.", file_size)
    if file_size >= MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(f"File size must be under {MAX_FILE_SIZE_HUMAN}.")

    return file


def prep_convert_args(
    source: str | Path,
    audio_events: bool,
    language: str | None,
) -> tuple[Path | None, ScribeArgs]:
    source = disambiguate_source(source)
    kwargs: ScribeArgs = {
        "model_id": "scribe_v1",
        "tag_audio_events": audio_events,
    }
    if language:
        kwargs["language_code"] = language

    if isinstance(source, str):
        kwargs["cloud_storage_url"] = source
        logger.debug("Prepared convert args: file=None, kwargs=%r.", kwargs)
        return None, kwargs

    logger.debug("Prepared convert args: file=%r, kwargs=%r.", source, kwargs)
    return source, kwargs


@asynccontextmanager
async def async_open_rb(path: Path) -> AsyncIterator[BinaryIO]:
    loop = asyncio.get_running_loop()
    file = await loop.run_in_executor(None, lambda: path.open("rb"))
    try:
        yield file
    finally:
        await loop.run_in_executor(None, file.close)
