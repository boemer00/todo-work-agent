"""Unit tests for Cloud Storage database utilities."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

from database import cloud_storage


def _install_storage_stub(monkeypatch: pytest.MonkeyPatch) -> dict:
    class DummyBlob:
        def __init__(self, exists: bool = True) -> None:
            self._exists = exists
            self.downloaded_path: Path | None = None
            self.uploaded_path: Path | None = None

        def exists(self) -> bool:
            return self._exists

        def download_to_filename(self, filename: str) -> None:
            self.downloaded_path = Path(filename)
            self.downloaded_path.write_text("stub")

        def upload_from_filename(self, filename: str) -> None:
            self.uploaded_path = Path(filename)

    class DummyBucket:
        def __init__(self, blob: DummyBlob) -> None:
            self._blob = blob
            self.requested_name: str | None = None

        def blob(self, name: str) -> DummyBlob:
            self.requested_name = name
            return self._blob

    class DummyClient:
        def __init__(self, blob: DummyBlob) -> None:
            self._blob = blob
            self.bucket_name: str | None = None

        def bucket(self, name: str) -> DummyBucket:
            self.bucket_name = name
            return DummyBucket(self._blob)

    blob = DummyBlob()
    client = DummyClient(blob)

    storage_module = ModuleType("storage")
    storage_module.Client = lambda: client  # type: ignore[assignment]

    google_module = ModuleType("google")
    cloud_module = ModuleType("cloud")
    cloud_module.storage = storage_module
    google_module.cloud = cloud_module

    monkeypatch.setitem(sys.modules, "google", google_module)
    monkeypatch.setitem(sys.modules, "google.cloud", cloud_module)
    monkeypatch.setitem(sys.modules, "google.cloud.storage", storage_module)

    return {"blob": blob, "client": client}


def test_is_cloud_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUD_RUN", "true")
    assert cloud_storage.is_cloud_environment() is True

    monkeypatch.setenv("CLOUD_RUN", "false")
    assert cloud_storage.is_cloud_environment() is False


def test_download_database_local_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUD_RUN", "false")
    monkeypatch.delenv("GOOGLE_CLOUD_STORAGE_BUCKET", raising=False)

    db_path = cloud_storage.download_database(db_name="local_mode_test.db")

    expected_dir = Path(cloud_storage.__file__).resolve().parent.parent / "data"
    assert Path(db_path) == expected_dir / "local_mode_test.db"


def test_download_database_cloud_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    stub = _install_storage_stub(monkeypatch)
    monkeypatch.setenv("CLOUD_RUN", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_STORAGE_BUCKET", "bucket-name")

    db_path = cloud_storage.download_database(
        db_name="cloud.db",
        local_path=str(tmp_path),
    )

    assert Path(db_path) == tmp_path / "cloud.db"
    assert stub["client"].bucket_name == "bucket-name"
    assert stub["blob"].downloaded_path == tmp_path / "cloud.db"


def test_upload_database_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    stub = _install_storage_stub(monkeypatch)
    monkeypatch.setenv("CLOUD_RUN", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_STORAGE_BUCKET", "bucket-name")

    db_file = tmp_path / "tasks.db"
    db_file.write_text("content")

    result = cloud_storage.upload_database(local_path=str(tmp_path))

    assert result is True
    assert stub["blob"].uploaded_path == db_file


def test_upload_database_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install_storage_stub(monkeypatch)
    monkeypatch.setenv("CLOUD_RUN", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_STORAGE_BUCKET", "bucket-name")

    result_missing_file = cloud_storage.upload_database(local_path=str(tmp_path))
    assert result_missing_file is False

    monkeypatch.setenv("GOOGLE_CLOUD_STORAGE_BUCKET", "")
    assert cloud_storage.upload_database(local_path=str(tmp_path)) is False


def test_sync_checkpoint_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    recorded_args: dict[str, str] = {}

    def fake_upload(db_name: str = "tasks.db", local_path: str = "/tmp") -> bool:
        recorded_args["db_name"] = db_name
        recorded_args["local_path"] = local_path
        return True

    monkeypatch.setattr(cloud_storage, "upload_database", fake_upload)

    assert cloud_storage.sync_checkpoint_database(local_path=str(tmp_path)) is True
    assert recorded_args == {"db_name": "checkpoints.db", "local_path": str(tmp_path)}


def test_get_cloud_db_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUD_RUN", "true")
    assert cloud_storage.get_cloud_db_path("remote.db") == "/tmp/remote.db"

    monkeypatch.setenv("CLOUD_RUN", "false")
    local_path = cloud_storage.get_cloud_db_path("local.db")

    expected_dir = Path(cloud_storage.__file__).resolve().parent.parent / "data"
    assert Path(local_path).parent == expected_dir
