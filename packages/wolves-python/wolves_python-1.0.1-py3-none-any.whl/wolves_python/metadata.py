from __future__ import annotations

from typing import Mapping

SDK_VERSION = "1.0.1"
SDK_TYPE = "wolves-python"

_metadata: dict[str, str] = {"sdk_version": SDK_VERSION, "sdk_type": SDK_TYPE}


class WolvesMetadataProvider:
    @staticmethod
    def get() -> dict[str, str]:
        return dict(_metadata)

    @staticmethod
    def add(additions: Mapping[str, str | None]) -> None:
        for key, value in additions.items():
            if value is None:
                continue
            _metadata[key] = value

