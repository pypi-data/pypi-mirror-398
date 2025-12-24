"""Manages multiple voices"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union, Type
from types import TracebackType

import sqlalchemy

from hlvox.multi_voice import MultiVoice
from hlvox.single_voice import SingleVoice
from hlvox.voice import Voice

log = logging.getLogger(__name__)


class DuplicateVoice(Exception):
    """Raised when duplicate voices are found"""


@dataclass
class RemoteDatabaseInfo:
    """Database connection information if using remote database (sql)"""

    name: str
    url: str
    port: int
    username: str
    password: str


@dataclass
class LocalDatabaseInfo:
    """Database info if using local file-based database (sqlite)"""

    base_path: Path


class Manager:
    """Manages multiple voices"""

    def __init__(
        self,
        voices_path: Union[Path, str],
        database_info: Optional[Union[LocalDatabaseInfo, RemoteDatabaseInfo]],
    ):
        self.voices_path = Path(voices_path)
        self._database_info = database_info
        self.voices: Dict[str, Union[MultiVoice, SingleVoice]] = {}

        self.scan_voices()

    def __enter__(self) -> "Manager":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.exit()

    def _create_db_path(self, databases_path: Path, voice_name: str) -> Path:
        db_path = databases_path / voice_name
        db_path.mkdir(parents=True, exist_ok=True)
        return db_path

    def _create_db(
        self,
        database_info: Union[LocalDatabaseInfo, RemoteDatabaseInfo],
        voice_name: str,
    ) -> sqlalchemy.engine.Engine:
        dbi = database_info
        if isinstance(dbi, LocalDatabaseInfo):
            path = self._create_db_path(
                databases_path=dbi.base_path, voice_name=voice_name
            )
            return sqlalchemy.create_engine(f"sqlite:///{path}/db.sqlite")
        return sqlalchemy.create_engine(
            f"postgresql+psycopg2://{dbi.username}:{dbi.password}@{dbi.url}:{dbi.port}/{dbi.name}",
            pool_pre_ping=True,
        )

    def scan_voices(self) -> None:
        """Scan for voices in the voices_path, updating the voices dictionary"""
        # Clean up existing voices and their database connections, if any
        for voice in self.voices.values():
            voice.exit()
        self.voices.clear()

        # Load new voices
        # This strangeness is to make mypy happy. There is probably a cleaner way to do it.
        single_voices = self._load_voices(self.voices_path)
        multi_voice = self._create_multi_voice(single_voices)
        self.voices.update(single_voices)
        self.voices["multi"] = multi_voice

    def _load_voices(self, path: Path) -> Dict[str, SingleVoice]:
        voices = {}
        voice_folders = list(x for x in path.iterdir() if x.is_dir())
        logging.info("Found %d voice folders", len(voice_folders))
        for voice_folder in voice_folders:
            voice_name = voice_folder.name.lower()
            logging.info("Loading voice %s", voice_name)
            if voice_name in voices:
                raise DuplicateVoice("Duplicate voice name found")

            database = None
            if self._database_info is not None:
                database = self._create_db(
                    database_info=self._database_info, voice_name=voice_name
                )
            new_voice = SingleVoice(
                name=voice_name, path=voice_folder, database=database
            )
            voices[new_voice.name] = new_voice
        logging.info("Loaded %d voices", len(voices))
        return voices

    def _create_multi_voice(self, voices: Dict[str, SingleVoice]) -> MultiVoice:
        database = None
        if self._database_info is not None:
            database = self._create_db(
                database_info=self._database_info, voice_name="multi"
            )
        return MultiVoice(
            voices=voices,
            database=database,
        )

    def get_voice_names(self) -> List[str]:
        """Gets names of available voices

        Returns:
            list -- list of voice name strings
        """

        voice_names = list(self.voices.keys())
        voice_names.sort()
        return voice_names

    def get_voice(self, name: str) -> Optional[Voice]:
        """Get voice of requested name

        Args:
            name ({string}): name of voice to get

        Returns:
            {voxvoice}: requested voice
        """
        if name in self.voices:
            return self.voices[name]
        return None

    def exit(self) -> None:
        """Exit all loaded voices"""
        for voice in self.voices.values():
            voice.exit()
