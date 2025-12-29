from dataclasses import dataclass
from ....framework import ConnectionSettings
from .model import FasterWhisperModel


@dataclass
class FasterWhisperSettings:
    connection: ConnectionSettings = ConnectionSettings(20102)

    models_to_download: tuple[FasterWhisperModel,...] = (

    )


