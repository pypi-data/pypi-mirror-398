"""Defines a unique voice"""

import copy
import enum
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import (
    BinaryIO,
    Dict,
    List,
    Optional,
    Tuple,
    TypeAlias,
    Union,
    Protocol,
    Type,
)
from types import TracebackType

import librosa
import numpy as np
import soundfile as sf  # type: ignore[import-untyped]
import sqlalchemy

log = logging.getLogger(__name__)


@dataclass
class Audio:
    """Represents an audio file"""

    data: np.ndarray
    sample_rate: float

    @classmethod
    def from_file(cls, file_path: Path) -> "Audio":
        """Create audio segment from file

        Args:
            file_path (Path): Path to audio file

        Returns:
            Audio: audio segment
        """
        data, sample_rate = librosa.load(file_path, mono=True)
        return Audio(data=data, sample_rate=sample_rate)

    @classmethod
    def create_silence(cls, duration: float, sample_rate: float) -> "Audio":
        """Create silence audio segment

        Args:
            duration (float): duration of silence
            sample_rate (float): sample rate of silence

        Returns:
            Audio: silence audio segment
        """
        data = np.zeros(int(duration * sample_rate))
        return Audio(data=data, sample_rate=sample_rate)

    def get_sample_rate(self) -> float:
        """Get sample rate of audio segment

        Returns:
            float: sample rate
        """
        return self.sample_rate

    def set_sample_rate(self, sample_rate: float) -> None:
        """Set sample rate of audio segment

        Args:
            sample_rate (int): sample rate to set

        Returns:
            Audio: audio segment with new frame rate
        """
        resampled_data = librosa.resample(
            y=self.data,
            orig_sr=self.sample_rate,
            target_sr=sample_rate,
        )
        self.data = resampled_data
        self.sample_rate = sample_rate

    def get_length_seconds(self) -> float:
        """Get length of audio segment in seconds

        Returns:
            float: length in seconds
        """
        return librosa.get_duration(y=self.data, sr=self.sample_rate)

    def export(self, output: BinaryIO, audio_format: str) -> None:
        """Export audio segment to file

        Args:
            output (BinaryIO): file to export to
            audio_format (str): audio format for export
        """
        sf.write(
            file=output,
            data=self.data,
            samplerate=self.sample_rate,
            format=audio_format,
        )

    def __add__(self, other: "Audio") -> "Audio":
        """Add two audio segments together

        Args:
            other (Audio): audio segment to add

        Returns:
            Audio: combined audio segment
        """
        # Set sample rate to highest common denominator
        if self.get_sample_rate() > other.get_sample_rate():
            other.set_sample_rate(self.get_sample_rate())
        elif self.get_sample_rate() < other.get_sample_rate():
            self.set_sample_rate(other.get_sample_rate())

        combined_data: np.ndarray = np.concatenate((self.data, other.data))
        return Audio(data=combined_data, sample_rate=self.get_sample_rate())


class ModifierClass(Protocol):
    IDENTIFIER: str

    @classmethod
    def from_str(cls, string: str) -> "Modifier": ...


@dataclass
class Modifier:
    """Base class for sound modifiers"""

    IDENTIFIER = ""

    @classmethod
    def from_str(cls, string: str) -> "Modifier":  # pylint: disable=unused-argument
        """Create from string representation"""
        return Modifier()

    def as_str(self) -> str:
        """Convert to string representation"""
        return ""

    def modify_audio(self, audio: Audio) -> Audio:
        """Modify audio segment

        Args:
            audio (Audio): audio segment to modify

        Returns:
            Audio: modified audio segment
        """
        return audio

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError


@dataclass
class SpeedChangeModifier(Modifier):
    """Modify speed of audio without changing pitch"""

    IDENTIFIER = "s"

    def __init__(self, speed_parameter: float) -> None:
        if speed_parameter <= 0.0:
            raise ModifierArgumentsInvalid

        self.speed_parameter = float(speed_parameter)

    @classmethod
    def from_str(cls, string: str) -> "SpeedChangeModifier":
        speed_parameter_str = string.strip(SpeedChangeModifier.IDENTIFIER)
        return SpeedChangeModifier(speed_parameter=float(speed_parameter_str))

    def as_str(self) -> str:
        return f"{self.IDENTIFIER}{self.speed_parameter}"

    def modify_audio(self, audio: Audio) -> Audio:
        stretched_data = librosa.effects.time_stretch(
            y=audio.data, rate=self.speed_parameter
        )
        return Audio(data=stretched_data, sample_rate=audio.sample_rate)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpeedChangeModifier):
            return False
        return self.speed_parameter == other.speed_parameter


@dataclass
class PitchChangeModifier(Modifier):
    """Modify pitch of audio without changing speed"""

    IDENTIFIER = "p"

    def __init__(self, pitch_parameter: float) -> None:
        self.pitch_parameter = float(pitch_parameter)

    @classmethod
    def from_str(cls, string: str) -> "PitchChangeModifier":
        pitch_parameter_str = string.strip(PitchChangeModifier.IDENTIFIER)
        return PitchChangeModifier(pitch_parameter=float(pitch_parameter_str))

    def as_str(self) -> str:
        return f"{self.IDENTIFIER}{self.pitch_parameter}"

    def modify_audio(self, audio: Audio) -> Audio:
        pitch_shifted_data = librosa.effects.pitch_shift(
            y=audio.data,
            sr=audio.sample_rate,
            n_steps=self.pitch_parameter,
        )
        return Audio(data=pitch_shifted_data, sample_rate=audio.sample_rate)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PitchChangeModifier):
            return False
        return self.pitch_parameter == other.pitch_parameter


class AcceleratorDirection(enum.Enum):
    """Direction for accelerator modifier"""

    FORWARD = enum.auto()
    REVERSE = enum.auto()

    @classmethod
    def from_str(cls, s: str) -> "AcceleratorDirection":
        """Convert from modifier string"""
        # TODO: this seems dumb
        if s == "f":
            return AcceleratorDirection.FORWARD
        if s == "r":
            return AcceleratorDirection.REVERSE
        raise AcceleratorDirectionInvalid

    def to_str(self) -> str:
        """Convert to modifier string"""
        # TODO: this seems dumb
        if self == AcceleratorDirection.FORWARD:
            return "f"
        if self == AcceleratorDirection.REVERSE:
            return "r"
        raise AcceleratorDirectionInvalid


@dataclass
class AcceleratorModifier(Modifier):
    """Accelerate a single word with modifiable pitch and speed curves"""

    IDENTIFIER = "a"

    def __init__(
        self, speed_increment: float, count: int, direction: AcceleratorDirection
    ) -> None:
        if speed_increment <= 0.0:
            raise ModifierArgumentsInvalid

        if count <= 1.0:
            raise ModifierArgumentsInvalid

        count = int(count)

        self.speed_increment = speed_increment
        self.count = count
        self.direction = direction

    # "hello|a2.0+100+r"
    # Where 2.0 is speed multiplier, 100 is the count, and r or f is forward or reverse. The last item is optional.
    @classmethod
    def from_str(cls, string: str) -> "AcceleratorModifier":
        parameter_str = string.strip(cls.IDENTIFIER)
        components = parameter_str.split("+")
        if len(components) < 2 or len(components) > 3:
            raise ModifierFormatNotCorrect
        speed_increment = float(components[0])
        count = int(components[1])
        direction = AcceleratorDirection.FORWARD
        if len(components) == 3:
            direction = AcceleratorDirection.from_str(components[2])

        return AcceleratorModifier(
            speed_increment=speed_increment, count=count, direction=direction
        )

    def as_str(self) -> str:
        return f"{self.IDENTIFIER}{self.speed_increment}+{self.count}+{self.direction.to_str()}"

    def modify_audio(self, audio: Audio) -> Audio:
        segment: Optional[Audio] = None
        increments: Union[range, reversed]

        if self.direction == AcceleratorDirection.REVERSE:
            increments = reversed(range(0, self.count))
        else:
            increments = range(0, self.count)

        for i in increments:
            if i == 0.0:
                speed_increment = 1.0
            else:
                speed_increment = i * self.speed_increment

            speed_modifier = SpeedChangeModifier(speed_parameter=speed_increment)

            modified_audio = copy.deepcopy(audio)
            if speed_modifier != 1.0:
                modified_audio = speed_modifier.modify_audio(audio=audio)
            else:
                modified_audio = copy.deepcopy(audio)

            if segment is None:
                segment = modified_audio
            else:
                segment += modified_audio

        if segment is None:
            raise ModifierArgumentsInvalid("No segments were created")

        return Audio(data=segment.data, sample_rate=segment.sample_rate)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AcceleratorModifier):
            return False
        return (
            self.speed_increment == other.speed_increment
            and self.count == other.count
            and self.direction == other.direction
        )


@dataclass
class VolumeChangeModifier(Modifier):
    """Modify volume of audio"""

    IDENTIFIER = "v"

    def __init__(self, volume_parameter: float) -> None:
        self.volume_parameter = float(volume_parameter)

    @classmethod
    def from_str(cls, string: str) -> "VolumeChangeModifier":
        volume_parameter_str = string.strip(VolumeChangeModifier.IDENTIFIER)
        return VolumeChangeModifier(volume_parameter=float(volume_parameter_str))

    def as_str(self) -> str:
        return f"{self.IDENTIFIER}{self.volume_parameter}"

    def modify_audio(self, audio: Audio) -> Audio:
        return Audio(
            data=audio.data * self.volume_parameter, sample_rate=audio.sample_rate
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VolumeChangeModifier):
            return False
        return self.volume_parameter == other.volume_parameter


class CutModifier(Modifier):
    """Cut start and end of audio"""

    IDENTIFIER = "c"

    def __init__(
        self, start_time_s: Optional[float], end_time_s: Optional[float]
    ) -> None:
        if start_time_s is None and end_time_s is None:
            raise ModifierArgumentsInvalid
        if start_time_s is not None and start_time_s < 0:
            raise ModifierArgumentsInvalid
        if end_time_s is not None and end_time_s < 0:
            raise ModifierArgumentsInvalid
        if (
            start_time_s is not None
            and end_time_s is not None
            and start_time_s >= end_time_s
        ):
            raise ModifierArgumentsInvalid

        self.start_time_s = start_time_s
        self.end_time_s = end_time_s

    @classmethod
    def from_str(cls, string: str) -> "CutModifier":
        start_time_s_str, end_time_s_str = string.strip(CutModifier.IDENTIFIER).split(
            "-"
        )
        if start_time_s_str == "":
            start_time_s = None
        else:
            start_time_s = float(start_time_s_str)
        if end_time_s_str == "":
            end_time_s = None
        else:
            end_time_s = float(end_time_s_str)
        return CutModifier(start_time_s=start_time_s, end_time_s=end_time_s)

    def as_str(self) -> str:
        start_time_s_str = "" if self.start_time_s is None else f"{self.start_time_s}"
        end_time_s_str = "" if self.end_time_s is None else f"{self.end_time_s}"
        return f"{self.IDENTIFIER}{start_time_s_str}-{end_time_s_str}"

    def modify_audio(self, audio: Audio) -> Audio:
        if self.start_time_s is None:
            start_index = 0
        else:
            start_index = int(self.start_time_s * audio.sample_rate)
        if self.end_time_s is None:
            end_index = len(audio.data)
        else:
            end_index = int(self.end_time_s * audio.sample_rate)
        return Audio(
            data=audio.data[start_index:end_index], sample_rate=audio.sample_rate
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CutModifier):
            return False
        return (
            self.start_time_s == other.start_time_s
            and self.end_time_s == other.end_time_s
        )


@dataclass
class NoOpModifier1(Modifier):
    """No-op modifier for testing"""

    IDENTIFIER = "z"

    def __init__(self, parameter: float) -> None:
        self.parameter = float(parameter)

    @classmethod
    def from_str(cls, string: str) -> "NoOpModifier1":
        parameter = string.strip(NoOpModifier1.IDENTIFIER)
        return NoOpModifier1(parameter=float(parameter))

    def as_str(self) -> str:
        return f"{self.IDENTIFIER}{self.parameter}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NoOpModifier1):
            return False
        return self.parameter == other.parameter


@dataclass
class NoOpModifier2(Modifier):
    """No-op modifier for testing"""

    IDENTIFIER = "x"

    def __init__(self, parameter: float) -> None:
        self.parameter = float(parameter)

    @classmethod
    def from_str(cls, string: str) -> "NoOpModifier2":
        parameter = string.strip(NoOpModifier2.IDENTIFIER)
        return NoOpModifier2(parameter=float(parameter))

    def as_str(self) -> str:
        return f"{self.IDENTIFIER}{self.parameter}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NoOpModifier2):
            return False
        return self.parameter == other.parameter


MODIFIERS: Dict[str, Type[ModifierClass]] = {
    CutModifier.IDENTIFIER: CutModifier,
    VolumeChangeModifier.IDENTIFIER: VolumeChangeModifier,
    SpeedChangeModifier.IDENTIFIER: SpeedChangeModifier,
    PitchChangeModifier.IDENTIFIER: PitchChangeModifier,
    AcceleratorModifier.IDENTIFIER: AcceleratorModifier,
    NoOpModifier1.IDENTIFIER: NoOpModifier1,
    NoOpModifier2.IDENTIFIER: NoOpModifier2,
}


Modifiers: TypeAlias = List[Modifier]


class Word:
    """Represents a word (or punctuation)"""

    def __init__(
        self,
        word: str,
        voice: Optional[str] = None,
        is_punctuation: bool = False,
        modifiers: Optional[Modifiers] = None,
    ) -> None:
        self.word = word
        self.voice = voice
        self.modifiers = modifiers if modifiers else []
        # Keep alphabetical order for string representation
        self.modifiers.sort(key=lambda m: m.IDENTIFIER)
        self.is_punctuation = is_punctuation

    def as_str(self, with_voice: bool = False) -> str:
        """Convert to string representation

        Args:
            with_voice (bool, optional): Include voice string. Defaults to False.

        Returns:
            str: string representation
        """
        voice_string = f"{self.voice}:" if (with_voice and self.voice) else ""
        modifiers_string = ""
        if self.modifiers:
            modifier_strings = ",".join(
                [modifier.as_str() for modifier in self.modifiers]
            )
            modifiers_string = f"|{modifier_strings}"
        return f"{voice_string}{self.word}{modifiers_string}"

    def __str__(self) -> str:
        return self.as_str(with_voice=True)

    def __repr__(self) -> str:
        return self.as_str(with_voice=True)

    def without_modifiers(self) -> "Word":
        """Get a copy of the word without modifiers

        Returns:
            Word: word without modifiers
        """
        return Word(
            word=self.word, voice=self.voice, is_punctuation=self.is_punctuation
        )

    # TODO: sorting does not take into account modifiers
    def __lt__(self, other: "Word") -> bool:
        return self.word < other.word

    def __gt__(self, other: "Word") -> bool:
        return self.word > other.word

    def __le__(self, other: "Word") -> bool:
        return self.word <= other.word

    def __ge__(self, other: "Word") -> bool:
        return self.word >= other.word

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Word):
            return False
        return (
            self.word == other.word
            and self.modifiers == other.modifiers
            and self.is_punctuation == other.is_punctuation
            and self.voice == other.voice
        )

    # TODO: test that this matches __eq__ behavior
    def __hash__(self) -> int:
        return hash(repr(self))


# How much delay should be added in place of punctuation (in milliseconds)
PUNCTUATION_TIMING_SECONDS = {
    ",": 0.250,
    ".": 0.500,
}

DB_NAME = "db.json"


class NoWordsFound(Exception):
    """Raised when a voice has no words"""


class DuplicateWords(Exception):
    """Raised when a voice has duplicate words"""


class InconsistentAudioFormats(Exception):
    """Raised when words have inconsistent audio formats"""


class NoAudioFormatFound(Exception):
    """Raised when no audio format can be found"""


class FailedToSplit(Exception):
    """Raised when a sentence cannot be split"""


class NoVoiceSpecified(Exception):
    """Raised when no voice is specified"""


class NoDatabaseSpecified(Exception):
    """No database connection was specified during init"""


class ModifierSyntaxError(Exception):
    """Raised when there is a problem with the modifier syntax"""


class SentenceIdNotFound(Exception):
    """Could not find a previously generated sentence with specified ID"""


class ModifierFormatNotCorrect(Exception):
    """Modifiers not provided in the correct format"""


class AcceleratorDirectionInvalid(Exception):
    """Invalid accelerator direction"""


class ModifierArgumentsInvalid(Exception):
    """Invalid modifier arguments and/or format"""


class DatabaseInsertFailed(Exception):
    """Raised when a sentence cannot be inserted into the database"""


@dataclass
class Sentence:
    """Represents a sentence and it's parts"""

    sentence: str
    sayable: List[Word]
    unsayable: List[Word]
    sayable_sentence: List[Word]
    audio: Optional[Audio] = None
    id: Optional[str] = None


@dataclass
class DatabaseConnection:
    """Stores info related to database connection"""

    engine: sqlalchemy.engine.Engine
    metadata: sqlalchemy.MetaData
    sentence_table: sqlalchemy.Table


class Voice:
    """Base class for Voice-like interfaces.
    Intended to involve generation of audio
    files from some source (files, web, etc).
    """

    def __init__(
        self,
        name: str,
        database: Optional[sqlalchemy.engine.Engine],
    ) -> None:
        self.name = name

        self._db: Optional[DatabaseConnection] = None
        if database is not None:
            metadata = sqlalchemy.MetaData()
            sentence_table = sqlalchemy.Table(
                self.name,
                metadata,
                sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
                sqlalchemy.Column(
                    "sentence", sqlalchemy.String, unique=True, nullable=False
                ),
            )
            metadata.create_all(database)
            self._db = DatabaseConnection(
                metadata=metadata,
                sentence_table=sentence_table,
                engine=database,
            )
        self.words: List[Word] = []
        self.categories: Dict[str, List[str]] = {}

    def __enter__(self) -> "Voice":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.exit()

    def exit(self) -> None:
        """Clean up and close voice"""
        if self._db is not None:
            self._db.engine.dispose()

    def _insert_sentence_into_db(self, sentence: str) -> int:
        if self._db is None:
            raise NoDatabaseSpecified
        ins = self._db.sentence_table.insert().values(sentence=sentence)
        with self._db.engine.begin() as conn:
            result = conn.execute(ins)
        if result.inserted_primary_key is None:
            raise DatabaseInsertFailed
        sentence_id = result.inserted_primary_key[0]
        if sentence_id is None:
            raise DatabaseInsertFailed
        return int(sentence_id)

    def _sentence_exists(self, sentence: str) -> bool:
        if self._db is None:
            raise NoDatabaseSpecified

        sel = self._db.sentence_table.select().where(
            self._db.sentence_table.c.sentence == sentence
        )
        with self._db.engine.connect() as conn:
            result = conn.execute(sel)
            # TODO: there should be a way to use `.Count()` here
        return bool(result.all())

    def _get_generated_sentences_list(self) -> list[str]:
        if self._db is None:
            raise NoDatabaseSpecified
        sel = self._db.sentence_table.select()
        with self._db.engine.connect() as conn:
            result = conn.execute(sel)
        return [r.sentence for r in result.all()]

    def _get_generated_sentences_dict(self) -> dict[int, str]:
        if self._db is None:
            raise NoDatabaseSpecified
        sel = self._db.sentence_table.select()
        with self._db.engine.connect() as conn:
            result = conn.execute(sel)
        return {r.id: r.sentence for r in result.all()}

    def _get_generated_sentence_from_id(self, sentence_id: str) -> Optional[str]:
        if self._db is None:
            raise NoDatabaseSpecified
        sel = self._db.sentence_table.select().where(
            # One day the ID might be a UUID string or something along those lines,
            # so we stay flexible on inputs and just convert to an int for now.
            self._db.sentence_table.c.id == int(sentence_id)
        )
        with self._db.engine.connect() as conn:
            result = conn.execute(sel)
        sentences = result.all()
        if not sentences:
            return None
        return str(sentences[0].sentence)

    def _get_sentence_info(self, words: List[Word]) -> Sentence:
        """Get basic sentence info for a given
        split sentence.

        Args:
            words (List[Word]): Words of sentence split into array

        Returns:
            Sentence: Sentence info
        """
        sayable_words, unsayable_worlds = self.get_sayable_unsayable(words)
        sayable_sent_arr = self._get_sayable_sentence_arr(words, sayable_words)
        sayable_sent_str = self._create_sentence_string(sayable_sent_arr)

        return Sentence(
            sentence=sayable_sent_str,
            sayable=sayable_words,
            unsayable=unsayable_worlds,
            sayable_sentence=sayable_sent_arr,
            audio=None,
            id=None,
        )

    def generate_audio_from_array(
        self, words: List[Word], dry_run: bool = False, save_to_db: bool = True
    ) -> Sentence:
        """Generates audio segment from sentence array.

        Args:
            words (List[str]): Words to try and turn into audio segment.
            dry_run (bool, optional): Skip actual segment generation. Defaults to False.

        Returns:
            Sentence: Sentence with audio segment.
        """
        sentence_info = self._get_sentence_info(words=words)

        if dry_run:
            return sentence_info

        log.debug("Generating %s", sentence_info.sentence)

        # Only create sentence if there are words to put in it
        if len(sentence_info.sayable) == 0:
            log.warning(
                "Can't say any words in %s, not generating", sentence_info.sentence
            )
            return sentence_info

        # Only bother inserting a sentence into the database if there is more than one word in it
        # TODO: test save_to_db
        if self._db and save_to_db and len(words) > 1:
            if not self._sentence_exists(sentence=sentence_info.sentence):
                sentence_id = self._insert_sentence_into_db(
                    sentence=sentence_info.sentence
                )
                sentence_info.id = str(sentence_id)
        words_audio = self._create_audio_segments(sentence_info.sayable_sentence)
        sentence_info.audio = self.assemble_audio_segments(words_audio)

        return sentence_info

    def _create_audio_segments(
        self,
        word_array: List[Word],  # pylint: disable=unused-argument
    ) -> List[Audio]:
        """Create audio segments for each entry in an array of words.

        Args:
            word_array (List[str]): Words to turn into audio segments.

        Returns:
            List[Audio]: Audio segments.
        """
        return []

    def generate_audio(self, sentence: str, dry_run: bool = False) -> Sentence:
        """Generates audio from the given sentence

        Args:
            sentence (string): Sentence string to be generated
            dry_run (bool, optional): Don't generate audio. Defaults to False.
        Returns:
            Sentence: Information about generated sentence.
        """
        log.info("Asked to generate %s", sentence)
        split_sentence = self._split_sentence(sentence)
        proc_sentence = self.process_sentence(split_sentence, voice=self.name)
        return self.generate_audio_from_array(
            words=proc_sentence,
            dry_run=dry_run,
        )

    def generate_audio_from_id(
        self, sentence_id: str, dry_run: bool = False
    ) -> Sentence:
        """Generate audio from an existing sentence, fetched by its ID

        Args:
            sentence_id (str): Existing sentence ID
            dry_run (bool, optional): Don't generate audio. Defaults to False.

        Raises:
            SentenceIdNotFound: Existing sentence ID not found in database

        Returns:
            Sentence: Information about generated sentence.
        """
        log.info("Fetching audio for ID %s", sentence_id)
        sentence = self._get_generated_sentence_from_id(sentence_id)
        if not sentence:
            raise SentenceIdNotFound
        return self.generate_audio(sentence=sentence, dry_run=dry_run)

    @staticmethod
    def _split_sentence(sentence: str) -> List[Word]:
        return [Word(word=word) for word in sentence.lower().rstrip().split(" ")]

    @staticmethod
    def _extract_modifiers(words: List[Word]) -> List[Word]:
        processed_words: list[Word] = []
        for word in words:
            if "|" not in word.word:
                processed_words.append(word)
                continue
            (word_string, _, modifiers_string) = word.word.rpartition("|")
            modifiers_strings = modifiers_string.split(",")

            # Dict so we can dedupe
            modifiers: dict[str, Modifier] = {}
            for modifier_string in modifiers_strings:
                modifier_class = MODIFIERS.get(modifier_string[0])
                # TODO: not bubbling up the invalid modifier doesn't seem right
                if modifier_class:
                    modifier = modifier_class.from_str(modifier_string)
                    if modifier.IDENTIFIER in modifiers:
                        continue
                    modifiers[modifier.IDENTIFIER] = modifier

            word.word = word_string
            # Preserve alphabetical order for string representation
            word.modifiers = list(modifiers.values())
            processed_words.append(word)
        return processed_words

    @staticmethod
    def process_sentence(split_sent: List[Word], voice: Optional[str]) -> List[Word]:
        """
        Takes a normally formatted sentence and breaks it into base elements

        Args:
            split_sent (List[str]): words in sentence

        Returns:
            List[Word]: array of elements in sentence
        """
        # TODO: This could use some rethinking. Should be easier to just always break punctuation marks
        # into their own elements, rather than selectively only dealing with trailing ones.
        log.info("Processing sentence '%s'", split_sent)

        # First pass for modifiers
        split_sent = Voice._extract_modifiers(words=split_sent)

        # Pull out punctuation
        reduced_sent: list[Word] = []
        for item in split_sent:
            word_string = item.word
            # find first punctuation mark, if any
            first_punct: Optional[str] = None
            try:
                first_punct = next(
                    (
                        punct
                        for punct in PUNCTUATION_TIMING_SECONDS
                        if punct in word_string
                    )
                )
            except StopIteration:
                pass

            if first_punct:
                # Get its index
                first_punct_ind = word_string.find(first_punct)

                # Special case: If this is a multi voice sentence,
                # we don't want to rip the voice definition out of a singe-punctuation
                # mark. IE vox:.
                # TODO: This is a bit hacky. Would be great if this method doesn't
                # have to know about multi-voice syntax.
                if first_punct_ind >= 2 and word_string[first_punct_ind - 1] == ":":
                    reduced_sent.append(
                        Word(
                            word=word_string[: first_punct_ind + 1],
                            voice=voice,
                            modifiers=item.modifiers,
                        )
                    )
                    if len(word_string) >= first_punct_ind:
                        first_punct_ind += 1
                else:
                    # Add everything before punct (the word, if any)
                    if word_string[:first_punct_ind]:
                        reduced_sent.append(
                            Word(
                                word=word_string[:first_punct_ind],
                                voice=voice,
                                modifiers=item.modifiers,
                            )
                        )

                # Add all the punctuation if its actually punctuation
                # TODO: Figure out if I want to deal with types like ".hello" throwing out all the characters after the period.
                for punct in word_string[first_punct_ind:]:
                    if punct in PUNCTUATION_TIMING_SECONDS:
                        reduced_sent.append(
                            Word(word=punct, voice=voice, is_punctuation=True)
                        )

            else:
                # TODO: copying from a Word to a Word like this is ugly
                reduced_sent.append(
                    Word(word=word_string, voice=voice, modifiers=item.modifiers)
                )

        # Clean blanks from reduced_sent
        reduced_sent = [value for value in reduced_sent if value.word != ""]

        log.info("Sentence processed: '%s'", reduced_sent)
        return reduced_sent

    def get_sayable_unsayable(self, words: List[Word]) -> Tuple[List[Word], List[Word]]:
        """Get words that are sayable or unsayable
        from a list of words.

        Args:
            words (List[Word]): Words to check.

        Returns:
            Tuple[List[Word], List[Word]]: Sayable and unsayable words.
        """
        # TODO: This shouldn't need two separate processings of the same sentence. Sets, people. Sets!
        sayable_words_set = set(self.words)
        sayable_words_set.update(
            [
                Word(word=punct, voice=self.name, is_punctuation=True)
                for punct in PUNCTUATION_TIMING_SECONDS
            ]
        )

        no_modifier_words = [word.without_modifiers() for word in words]
        words_set = set((dict.fromkeys(no_modifier_words)))  # removes duplicates

        unsayable_set = words_set - sayable_words_set
        sayable_set = words_set - unsayable_set
        unsayable = list(unsayable_set)
        unsayable.sort()
        sayable = list(sayable_set)
        sayable.sort()
        return sayable, unsayable

    def _get_sayable_sentence_arr(
        self, words: List[Word], sayable_words: List[Word]
    ) -> List[Word]:
        """Removes words from sentence array that are not sayable.

        Args:
            words (List[Word]): Array of words in sentence, in order.
            sayable_words (List[Word]): Words from sentence that can actually be said.

        Returns:
            List[Word]: Words in sentence that are sayable, in order.
        """
        # TODO: This is just a simple set operation. Function probably isn't needed. At least change to using a set.
        return [
            word
            for word in words
            if Word(
                word=word.word, voice=word.voice, is_punctuation=word.is_punctuation
            )
            in sayable_words
        ]

    def _create_sentence_string(self, words: List[Word]) -> str:
        """Joins sentence array into a string.

        Args:
            words (List[str]): Words in sentence, in order.

        Returns:
            str: Sentence string.
        """
        if len(words) == 1:
            return words[0].as_str(with_voice=False)
        return " ".join([word.as_str(with_voice=False) for word in words])

    def get_generated_sentences(self) -> List[str]:
        """Gets the previously generated sentence strings

        Returns:
            List[str]: List of sentence strings generated previously
        """
        return self._get_generated_sentences_list()

    def get_generated_sentences_dict(self) -> Dict[int, str]:
        """Gets the previously generated sentence strings
        along with their corresponding ID in the database

        Returns:
            Dict[int, str]: Dict of sentence and id pairs
        """
        return self._get_generated_sentences_dict()

    @staticmethod
    def assemble_audio_segments(segments: List[Audio]) -> Audio:
        """Assemble audio segments into one audio segment.

        Args:
            segments (List[Audio]): Segments to assemble.

        Returns:
            Audio: Assembled audio segment.
        """
        # We set all audio segments to the lowest common frame rate
        # to avoid some really ugly artifacting when a low frame rate
        # clip is appended to a high frame rate one.
        frame_rates = [word.get_sample_rate() for word in segments]
        frame_rate = min(frame_rates)

        sentence_audio = segments.pop(0)
        if sentence_audio.get_sample_rate() != frame_rate:
            sentence_audio.set_sample_rate(frame_rate)
        for word_audio in segments:
            if word_audio.get_sample_rate() != frame_rate:
                word_audio.set_sample_rate(frame_rate)
            sentence_audio = sentence_audio + word_audio

        return sentence_audio
