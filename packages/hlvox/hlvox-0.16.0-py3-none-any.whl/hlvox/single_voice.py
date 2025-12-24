"""Contains SingleVoice class, which is used to index a folder of voice audio files
and generate audio from them given a sentence string.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional, Tuple

import sqlalchemy

from .voice import (
    PUNCTUATION_TIMING_SECONDS,
    Audio,
    DuplicateWords,
    InconsistentAudioFormats,
    NoAudioFormatFound,
    NoWordsFound,
    Voice,
    Word,
)

log = logging.getLogger(__name__)


class SingleVoice(Voice):
    """Comprises all information and methods
    needed to index a folder of voice audio files
    and generate audio from them given a sentence string.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self, name: str, path: Path, database: Optional[sqlalchemy.engine.Engine]
    ):
        """
        Args:
            name: Name of voice
            path (Path): Path to folder of voice audio files.
            database (Optional[DatabaseConnection]): Database connection information.
                If none provided, no database will be used and no data will persist.
        """
        super().__init__(name=name, database=database)
        self.path = path

        self.info_path = self.path.joinpath("info/")
        self.info_name = "info.json"

        self.scan_files()

    def scan_files(self) -> None:
        """
        Scans the voice's files to pick up any new or modified audio files.
        This will update the word dictionary, categories, and audio data.
        """
        self._word_dict, self.categories = self._build_word_dict(self.path)
        self._word_audio, self._sample_rate = self._get_word_audio(self._word_dict)

        self.words = self._get_words()

        self._read_info(self.info_path, self.info_name)

    def _build_word_dict(
        self, path: Path
    ) -> Tuple[Dict[str, Path], Dict[str, list[str]]]:
        """Builds dictionary of all available words and categories.

        Args:
            path (Path): Path to folder of voice audio files, or folders of voices files.

        Raises:
            DuplicateWords: Raised if there are duplicate filenames present.
            NoWordsFound: Raised if no words are found.

        Returns:
            Tuple[Dict[str, Path], Dict[str, list[str]]]: Dict of {filepath: word} associations and {category: [words]}.
        """
        word_dict: Dict[str, Path] = {}
        categories: defaultdict[str, list[str]] = defaultdict(list)

        for word_path in path.glob("**/*"):
            if word_path.is_dir():
                continue
            if word_path.parent.name == "info":
                continue
            word = word_path
            name = str(word.stem).lower()
            if name in word_dict:
                raise DuplicateWords(f"Word {name} is duplicated")
            category = ""
            if word.parent != path:
                category = word.parent.name

            word_dict[name] = word
            if category:
                categories[category].append(name)
                # This is probably bad
                categories[category].sort()

        if len(word_dict) == 0:
            log.error("No words found")
            raise NoWordsFound

        return word_dict, categories

    def _get_word_audio(
        self, word_dict: Dict[str, Path]
    ) -> Tuple[Dict[str, Audio], float]:
        """Builds dictionary of words and their audio data.

        Args:
            word_dict (Dict[str, Path]): Dict of {filepath: word} associations.

        Returns:
            Tuple[Dict[str, Audio], float]: Dict of {word: Audio} associations and sample rate.
        """
        word_audio: dict[str, Audio] = {}
        sample_rates: list[float] = []
        for word, path in word_dict.items():
            word_audio[word] = Audio.from_file(file_path=path)
            sample_rates.append(word_audio[word].get_sample_rate())

        sample_rate = max(sample_rates)
        for word, audio in word_audio.items():
            if audio.get_sample_rate() != sample_rate:
                audio.set_sample_rate(sample_rate)

        return word_audio, sample_rate

    def _read_info(self, path: Path, info_name: str) -> None:
        """Reads info file (if it exists)
        Args:
            path (Path): Path where info file resides.
            info_name (str): Name of info file.
        """
        # TODO: Allow arbitrary groupings of words
        info_path = path.joinpath(info_name)
        if info_path.exists():
            with open(info_path, "r", encoding="UTF-8") as info_file:
                # TODO: we don't currently use this. Leaving it be to validate format
                json.load(info_file)

    def _find_audio_format(self, word_dict: Dict[str, Path]) -> str:
        """Determines audio format of voice audio files.

        Args:
            word_dict (Dict[str, Path]): Dict of {filepath: word} associations.

        Raises:
            NoAudioFormatFound: Raised if no audio format can be determined.
            InconsistentAudioFormats: Raised if there are inconsistent audio formats.

        Returns:
            str: Audio format.
        """
        file_format: Optional[str] = None
        for path in word_dict.values():
            if file_format is None:
                file_format = path.suffix[1:]
            else:
                if str(file_format) != str(path.suffix[1:]):
                    log.error(
                        "Inconsistent audio formats in the word dict. File %s does not match expected format of %s",
                        path,
                        file_format,
                    )
                    raise InconsistentAudioFormats
        if not file_format:
            raise NoAudioFormatFound

        log.info("Audio format found: %s", file_format)
        return file_format

    # TODO: sweep docstrings for str -> Word

    def _get_words(self) -> list[Word]:
        """Gets the available words for the voice

        Returns:
            list[Word]: Words available to the voice
        """
        word_list = list(self._word_dict.keys())
        word_list.sort()
        return [Word(word=word, voice=self.name) for word in word_list]

    def _create_audio_segments(self, word_array: list[Word]) -> list[Audio]:
        words_audio: list[Audio] = []
        for word in word_array:
            if word.is_punctuation:
                silent_segment = Audio.create_silence(
                    duration=PUNCTUATION_TIMING_SECONDS[word.word],
                    sample_rate=self._sample_rate,
                )
                words_audio.append(silent_segment)
            else:
                audio = self._word_audio[word.word]

                for modifier in word.modifiers:
                    audio = modifier.modify_audio(audio)

                words_audio.append(audio)
        return words_audio
