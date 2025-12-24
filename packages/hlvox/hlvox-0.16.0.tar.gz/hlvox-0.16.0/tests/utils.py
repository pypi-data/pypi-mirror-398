"""Utilities used for testing"""

import json
import struct
import wave
from pathlib import Path
from typing import Dict, List


def create_word_files(
    audio_path: Path, files: List[str], touch_only: bool = False
) -> List[Path]:
    """Create word files for testing

    Args:
        audio_path (Path): Path to create word files in
        word_strings (List[str]): Words to create files for

    Returns:
        List[Path]: List of paths to created word files
    """
    word_files = []
    for file in files:
        filepath = audio_path.joinpath(file)
        word_files.append(filepath)

        if touch_only:
            filepath.touch()
            continue
        savefile = wave.open(str(filepath), "w")

        # channels, datasize (16 bit), sample rate, number of samples
        savefile.setparams((1, 2, 11025, 500, "NONE", "Uncompressed"))
        savefile.writeframes(struct.pack("h", 1))
        savefile.close()
    return word_files


def create_voice_files(
    base_path: Path,
    files: List[str],
    voice_name: str = "voice",
    touch_only: bool = False,
) -> Path:
    """Create voice files for testing

    Args:
        base_path (Path): Path to create voice folder at
        files (List[str]): Files to add to voice folder
        voice_name (str, optional): Voice name. Defaults to 'voice'.
        touch_only (bool, optional): Only touch voice files, don't use actual audio. Defaults to False.

    Returns:
        Path: Path to voice folder
    """
    audio_path = base_path.joinpath(voice_name)
    audio_path.mkdir()

    create_word_files(audio_path=audio_path, files=files, touch_only=touch_only)

    return audio_path


def create_category_files(
    base_path: Path, category_files: Dict[str, List[str]], voice_name: str = "voice"
) -> Path:
    """Create category files for testing

    Args:
        base_path (Path): Path to create category files in
        category_files (Dict[str, List[str]]): Files to create
        voice_name (str, optional): Voice name. Defaults to 'voice'.

    Returns:
        Path: Path to category files
    """
    audio_path = base_path.joinpath(voice_name)
    audio_path.mkdir()

    for category, files in category_files.items():
        create_voice_files(base_path=audio_path, files=files, voice_name=category)

    return audio_path


def create_info(info: dict, audio_path: Path) -> None:
    """Create info file for testing

    Args:
        info (dict): Info contents
        audio_path (Path): Path to create info file in
    """
    info_dir = Path(audio_path).joinpath("info/")

    info_dir.mkdir(parents=True, exist_ok=True)

    info_file = info_dir.joinpath("info.json")

    with open(info_file, "w", encoding="UTF-8") as file:
        json.dump(info, file)
