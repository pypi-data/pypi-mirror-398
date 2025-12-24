"""Command line interface for hlvox"""

import argparse
import logging
import sys
from pathlib import Path

from hlvox.manager import Manager
from hlvox.single_voice import SingleVoice

log = logging.getLogger(__name__)


def single_voice(voice_dir: Path, sentence: str, audio_format: str) -> None:
    """Generate audio from a single voice"""
    voice_dir = Path(voice_dir)
    if not voice_dir.is_dir():
        log.error("Voice dir at %s does not exist!", voice_dir)
        sys.exit(1)

    selected_voice = SingleVoice(name=voice_dir.name, path=voice_dir, database=None)
    generated_sentence = selected_voice.generate_audio(sentence)
    if generated_sentence.audio is None:
        sys.exit(1)
    if generated_sentence.unsayable:
        log.warning("Could not say %s", generated_sentence.unsayable)

    output_path = Path.cwd().joinpath(f"{generated_sentence.sentence}.{audio_format}")

    with output_path.open("wb") as f:
        generated_sentence.audio.export(f, audio_format=audio_format)


def multi_voice(voices_dir: Path, voice: str, sentence: str, audio_format: str) -> None:
    """Generate audio from multiple voices"""
    voices_dir = Path(voices_dir)
    if not voices_dir.is_dir():
        log.error("Voices dir at %s does not exist!", voices_dir)
        sys.exit(1)

    manager = Manager(
        voices_path=voices_dir,
        database_info=None,
    )

    loaded_voice = manager.get_voice(voice)
    if loaded_voice is None:
        log.error("Voice %s was not found", loaded_voice)
        sys.exit(1)

    # TODO: reduce duplication between single and multi voice
    gen_sentence = loaded_voice.generate_audio(sentence)
    if gen_sentence.audio is None:
        log.error("Cannot generate %s: %s", gen_sentence.sentence, sentence)
        sys.exit(1)
    if gen_sentence.unsayable:
        log.warning("Could not say %s", gen_sentence.unsayable)

    # Paths can't have : in them, so replace with % as a stand-in
    sanitized_sentence = gen_sentence.sentence.replace(":", "%")
    output_path = Path.cwd().joinpath(f"{sanitized_sentence}.{audio_format}")

    log.info("Exporting to %s", output_path)
    with output_path.open("wb") as f:
        gen_sentence.audio.export(f, audio_format=audio_format)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("numba").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(
        description="Generate a sentence using a voice or multiple voices"
    )
    parser.add_argument(
        "-s",
        "--single-voice-dir",
        type=str,
        required=False,
        help="Path to folder with voice audio files (generate from a single voice)",
    )
    parser.add_argument(
        "-m",
        "--multiple-voices-dir",
        type=str,
        required=False,
        help="Path to folders with voice audio file folders (generate from one of multiple voices)",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        required=False,
        default="wav",
        help="Audio format to export as",
    )
    parser.add_argument(
        "-v",
        "--voice",
        required=False,
        type=str,
        help="Voice to use when generating audio (if using multiple voice manager)",
    )
    parser.add_argument("sentence", type=str)
    args = parser.parse_args()

    if args.single_voice_dir:
        single_voice(
            voice_dir=Path(args.single_voice_dir),
            sentence=args.sentence,
            audio_format=args.format,
        )
    elif args.multiple_voices_dir:
        if not args.voice:
            log.error("Specify a voice to use!")
            sys.exit(1)
        multi_voice(
            voices_dir=Path(args.multiple_voices_dir),
            voice=args.voice,
            sentence=args.sentence,
            audio_format=args.format,
        )
    else:
        log.error("Specify either a single or multiple voice dir!")
        sys.exit(1)
