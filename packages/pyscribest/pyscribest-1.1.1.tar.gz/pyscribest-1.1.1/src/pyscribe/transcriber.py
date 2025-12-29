from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from pyscribe.utils import async_open_rb, prep_convert_args

if TYPE_CHECKING:
    from pathlib import Path

    from elevenlabs import AsyncElevenLabs, ElevenLabs, SpeechToTextChunkResponseModel


logger = logging.getLogger(__name__)


def transcribe(
    client: ElevenLabs,
    file_uri: str | Path,
    audio_events: bool = False,
    language: str | None = None,
) -> str:
    file, kwargs = prep_convert_args(file_uri, audio_events, language)
    logger.info("Transcribing... This may take a while depending on the file size.")
    if not file:
        response = client.speech_to_text.convert(**kwargs)
        return cast("SpeechToTextChunkResponseModel", response).text

    with file.open("rb") as audio_file:
        response = client.speech_to_text.convert(file=audio_file, **kwargs)
        return cast("SpeechToTextChunkResponseModel", response).text


async def atranscribe(
    client: AsyncElevenLabs,
    file_uri: str | Path,
    audio_events: bool = True,
    language: str | None = None,
) -> str:
    file, kwargs = prep_convert_args(file_uri, audio_events, language)
    logger.info("Transcribing... This may take a while depending on the file size.")
    if not file:
        response = await client.speech_to_text.convert(**kwargs)
        return cast("SpeechToTextChunkResponseModel", response).text

    async with async_open_rb(file) as audio_file:
        response = await client.speech_to_text.convert(file=audio_file, **kwargs)
        return cast("SpeechToTextChunkResponseModel", response).text
