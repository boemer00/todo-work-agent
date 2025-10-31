"""Tests for `database.connection` helpers."""

from __future__ import annotations

import os
from pathlib import Path

from database import connection


def test_get_db_path_cloud_mode(monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_RUN", "true")

    path = connection.get_db_path("cloud.db")

    assert path == "/tmp/cloud.db"


def test_get_db_path_local_mode(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CLOUD_RUN", "false")

    created_dirs: list[Path] = []

    def fake_makedirs(path: str, exist_ok: bool = False) -> None:
        created_dirs.append(Path(path))

    monkeypatch.setattr(connection.os, "makedirs", fake_makedirs)

    path = Path(connection.get_db_path("local.db"))

    assert path.name == "local.db"
    assert path.parent.name == "data"
    assert created_dirs and created_dirs[0].name == "data"
