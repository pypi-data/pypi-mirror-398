"""Voice class that uses other voices to assemble
multi-voice sentences.
"""

import logging
from typing import Dict, Optional, Tuple
import sqlalchemy

from .single_voice import SingleVoice
from .voice import (
    PUNCTUATION_TIMING_SECONDS,
    Audio,
    FailedToSplit,
    NoVoiceSpecified,
    Sentence,
    Voice,
    Word,
)

log = logging.getLogger(__name__)


class MultiVoice(Voice):
    """Voice class that uses other voices to assemble
    multi-voice sentences.

    Example: vox:hello hev:there
    Generates a sentence with one word from a voice
    called "vox" and another from a voice called "hev."
    """

    def __init__(
        self, voices: dict[str, SingleVoice], database: sqlalchemy.engine.Engine | None
    ):
        """
        Args:
            voices (Dict[str, SingleVoice]): Voices to use to assemble sentences.
            database (Optional[sqlalchemy.engine.Engine]): Database connection information.
                If none provided, no database will be used and no data will persist.
        """
        super().__init__(name="multi", database=database)
        self._voices = voices

        self.words = self._get_words(voices)

    def _get_words(self, voices: Dict[str, SingleVoice]) -> list[Word]:
        words = []
        for _, voice in voices.items():
            voice_words = voice.words.copy()
            words.extend(voice_words)
        return words

    def _get_sentence_info(self, words: list[Word]) -> Sentence:
        # TODO: There is a good amount of double-processing going on here
        words_and_voices = self._get_word_voice_assignment(words)
        sayable_words, unsayable_words = self.get_sayable_unsayable(words)
        sayable_sent_arr = [
            word_voice
            for word_voice in words_and_voices
            if word_voice.without_modifiers() in sayable_words
        ]
        combined_voice_sentences = self.get_combined_voice_sentences(words_and_voices)
        sentence_arr = []
        for voice, sentence_words in combined_voice_sentences:
            voice_sentence_segment = (
                f"{voice.name}:{' '.join([word.as_str() for word in sentence_words])}"
            )
            sentence_arr.append(voice_sentence_segment)

        sayable_sent_str = " ".join(sentence_arr)

        return Sentence(
            sentence=sayable_sent_str,
            sayable=sayable_words,
            unsayable=unsayable_words,
            sayable_sentence=sayable_sent_arr,
            audio=None,
        )

    def get_sayable_unsayable(self, words: list[Word]) -> Tuple[list[Word], list[Word]]:
        sayable = []
        unsayable = []
        words_and_voices = self._get_word_voice_assignment(words=words)
        combined_voice_sentences = self.get_combined_voice_sentences(words_and_voices)
        for voice, sentence_words in combined_voice_sentences:
            voice_sayable, voice_unsayable = voice.get_sayable_unsayable(sentence_words)
            sayable.extend(voice_sayable)
            unsayable.extend(voice_unsayable)
        sayable.sort()
        unsayable.sort()
        return sayable, unsayable

    def _create_audio_segments(self, word_array: list[Word]) -> list[Audio]:
        combined_voice_sentences = self.get_combined_voice_sentences(word_array)
        return self.get_combined_audio(
            voice_sentences=combined_voice_sentences,
        )

    def _get_word_voice_assignment(self, words: list[Word]) -> list[Word]:
        """Determines voice for each word in a list separated
        from a raw sentence. Only the first word must have a voice
        assignment, further assignments are inferred.

        Example: vox:hello there hev:doctor freeman
        The first two words are assigned to vox, second two to hev

        Args:
            words (List[Word]): Words to determine voice assignment of

        Raises:
            FailedToSplit: Raised if unable to split a word/voice assignment.
            NoVoiceSpecified: Raised if initial voice cannot be determined.

        Returns:
            List[Word]: word:voice assignments
        """
        words_and_voices = []

        current_voice: Optional[SingleVoice] = None
        for word_maybe_voice in words:
            word_split = word_maybe_voice.word.split(":")
            word: Optional[Word] = None
            word_str: Optional[str] = None
            if len(word_split) == 2:
                voice_name = word_split[0]
                if voice_name not in self._voices:
                    raise NoVoiceSpecified(f"Voice {voice_name} not found")
                current_voice = self._voices[voice_name]
                word_str = word_split[1]
            elif len(word_split) == 1:
                word_str = word_split[0]

            if not word_str:
                raise FailedToSplit
            if not current_voice:
                raise NoVoiceSpecified("No voice specified for word")

            is_punctuation = word_str in PUNCTUATION_TIMING_SECONDS
            modifiers = word_maybe_voice.modifiers if not is_punctuation else []
            word = Word(
                word=word_str,
                voice=current_voice.name,
                modifiers=modifiers,
                is_punctuation=is_punctuation,
            )

            words_and_voices.append(word)

        return words_and_voices

    def get_combined_voice_sentences(
        self, words: list[Word]
    ) -> list[Tuple[SingleVoice, list[Word]]]:
        """Turns individual word:voice assignments into
        combined sentences for each word in sequence:

        Example: vox:hello vox:there hev:doctor hev:freeman vox:boop
        Returns vox:[hello, there] hev:[doctor freeman] vox:[boop]

        Args:
            words (List[Word]): Word:voice assignments

        Returns:
            List[Tuple[SingleVoice, List[Word]]]: Voice:sentence assignments
        """
        current_voice: Optional[SingleVoice] = None
        current_voice_sentence: list[Word] = []
        voice_sentences = []
        for word in words:
            if not current_voice:
                if word.voice not in self._voices:
                    raise NoVoiceSpecified(f"Voice {word.voice} not found")
                current_voice = self._voices[word.voice]
            if word.voice == current_voice.name:
                current_voice_sentence.append(word)
            else:
                voice_sentences.append((current_voice, current_voice_sentence))
                if word.voice not in self._voices:
                    raise NoVoiceSpecified(f"Voice {word.voice} not found")
                current_voice = self._voices[word.voice]
                current_voice_sentence = [word]
        if current_voice and current_voice_sentence:
            voice_sentences.append((current_voice, current_voice_sentence))
        return voice_sentences

    def get_combined_audio(
        self, voice_sentences: list[Tuple[SingleVoice, list[Word]]]
    ) -> list[Audio]:
        """Generates audio segments for each voice sentence

        Args:
            voice_sentences (List[Tuple[SingleVoice, List[str]]]): Voice:sentence assignments

        Returns:
            List[Audio]: List of generated audio segments
        """
        audio_segments = []
        for voice, words in voice_sentences:
            sentence = voice.generate_audio_from_array(words, save_to_db=False)
            if sentence.audio:
                audio_segments.append(sentence.audio)
        sample_rate = max(audio.get_sample_rate() for audio in audio_segments)
        for audio in audio_segments:
            if audio.get_sample_rate() != sample_rate:
                audio.set_sample_rate(sample_rate)
        return audio_segments
