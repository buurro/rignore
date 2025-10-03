from __future__ import annotations

from pathlib import Path

import pytest
from typing_extensions import LiteralString

import rignore

FOLDER_STRUCTURE = """
some_file.txt
some_folder/
some_folder/some_file.txt
some_folder/some_folder/
some_folder/some_folder/some_file.txt
an_image.jpg
.include-me
""".strip()


@pytest.fixture
def folder_structure() -> list[LiteralString]:
    return FOLDER_STRUCTURE.splitlines()


@pytest.fixture
def folder(tmp_path: str, folder_structure: list[str]) -> Path:
    folder = Path(tmp_path)

    for path in folder_structure:
        if path.endswith("/"):
            (folder / path).mkdir()
        else:
            (folder / path).touch()

    return folder


def test_basic_walk(folder: Path, folder_structure: list[str]):
    paths = list(rignore.walk(folder))

    expected_paths = [folder] + [folder / path for path in folder_structure]

    assert len(paths) == 7

    for path in paths:
        assert path in expected_paths


def test_filter_entry(folder: Path):
    def should_exclude(entry: Path) -> bool:
        return entry.name == "some_folder"

    paths = list(rignore.walk(folder, should_exclude_entry=should_exclude))

    expected_paths = [
        folder,
        folder / "some_file.txt",
        folder / "an_image.jpg",
    ]

    assert len(paths) == 3

    for path in paths:
        assert path in expected_paths


def test_overrides(tmp_path: Path):
    folder = Path(tmp_path)

    # Create a .gitignore that ignores .env files
    gitignore = folder / ".gitignore"
    gitignore.write_text("*.env\n")

    # Create both an ignored file and one that should be included
    (folder / ".env").touch()
    (folder / ".env.example").touch()
    (folder / "regular.txt").touch()

    # Without overrides, .env and .env.example should be ignored
    paths_without_override = list(rignore.walk(folder, read_git_ignore=True))
    names_without = {p.name for p in paths_without_override}

    assert ".env" not in names_without
    assert ".env.example" not in names_without
    assert "regular.txt" in names_without

    # With overrides, only files matching the patterns will be included
    # This includes .env.example (which was gitignored) and regular.txt
    paths_with_override = list(
        rignore.walk(
            folder,
            read_git_ignore=True,
            overrides=[".env.example", "*.txt", ".include-me"],
        )
    )
    names_with = {p.name for p in paths_with_override}

    assert ".env" not in names_with
    assert ".env.example" in names_with
    assert "regular.txt" in names_with
