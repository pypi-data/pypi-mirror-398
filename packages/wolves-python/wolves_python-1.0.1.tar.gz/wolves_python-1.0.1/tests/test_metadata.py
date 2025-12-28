from __future__ import annotations

from wolves_python.metadata import SDK_TYPE, SDK_VERSION, WolvesMetadataProvider


def test_metadata_provider_additions_are_reflected() -> None:
    base = WolvesMetadataProvider.get()
    assert base["sdk_type"] == SDK_TYPE
    assert base["sdk_version"] == SDK_VERSION

    WolvesMetadataProvider.add({"test_key": "test_value", "ignore_me": None})
    updated = WolvesMetadataProvider.get()
    assert updated["test_key"] == "test_value"
    assert updated.get("ignore_me") is None
