"""Test voice manager"""

# pylint: disable=missing-function-docstring,disable=missing-class-docstring
# pylint: disable=too-few-public-methods
from typing import Generator
import sys
from pathlib import Path

import pytest

import hlvox
import hlvox.manager

from . import utils as th

test_files = {"v1": ["hello.wav"], "v2": ["hello.wav"], "v3": ["hello.wav"]}


@pytest.fixture(name="manager")
def manager_fixture(tmp_path: Path) -> Generator[hlvox.manager.Manager, None, None]:
    voices_dir = tmp_path.joinpath("voices")
    voices_dir.mkdir()
    for voice, words in test_files.items():
        th.create_voice_files(voices_dir, words, voice)
    manager = hlvox.manager.Manager(voices_path=voices_dir, database_info=None)
    yield manager
    manager.exit()


class TestVoiceImport:
    def test_voice_list(self, manager: hlvox.manager.Manager) -> None:
        expected_voices = list(test_files.keys())
        expected_voices.append("multi")
        expected_voices.sort()
        assert manager.get_voice_names() == expected_voices

        # Add a new voice
        new_voice_name = "v4"
        new_words = ["hello.wav"]
        new_voice_path = th.create_voice_files(
            manager.voices_path, new_words, new_voice_name
        )
        manager.scan_voices()
        new_expected_voices = expected_voices.copy()
        new_expected_voices.append(new_voice_name)
        new_expected_voices.sort()
        assert manager.get_voice_names() == new_expected_voices

        # Remove a voice
        for file in new_voice_path.glob("*"):
            file.unlink()
        new_voice_path.rmdir()
        manager.scan_voices()
        assert manager.get_voice_names() == expected_voices


class TestGetVoice:
    def test_get_voice(self, manager: hlvox.manager.Manager) -> None:
        voice = manager.get_voice("v1")

        assert voice is not None
        assert voice.name == "v1"

    def test_get_wrong_voice(self, manager: hlvox.manager.Manager) -> None:
        voice = manager.get_voice("nope")

        assert not voice


class TestDuplicatevoice:
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows is not case sensitive so duplicates cant exist",
    )
    def test_case_diff(self, tmp_path: Path) -> None:
        voices_dir = tmp_path.joinpath("voices")
        voices_dir.mkdir()
        th.create_voice_files(voices_dir, ["hello.wav"], "AHH")
        th.create_voice_files(voices_dir, ["hello.wav"], "ahh")
        th.create_voice_files(voices_dir, ["hello.wav"], "aHH")

        with pytest.raises(hlvox.manager.DuplicateVoice):
            hlvox.manager.Manager(voices_path=voices_dir, database_info=None)
