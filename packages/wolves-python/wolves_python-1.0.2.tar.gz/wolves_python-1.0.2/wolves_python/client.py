from __future__ import annotations

import concurrent.futures
import json
import time

from .experiment import Experiment
from .future import WolvesFuture
from .network import API_DEV, Network
from .runtime import AsyncRuntime
from .store import Store
from .types import WolvesUser
from .types import WolvesEvent
from .event_logger import EventLogger


class WolvesClient:
    def __init__(self, sdk_key: str, api: str | None = None) -> None:
        self._sdk_key = sdk_key
        self._api = api or API_DEV
        self._runtime = AsyncRuntime()
        self._network = Network(sdk_key, api=self._api)
        self._store = Store()
        self._logger = EventLogger(self._network, self._runtime)
        self._initialized = False
        self._user: WolvesUser | None = None

    def initialize(self, user: WolvesUser) -> WolvesFuture[bool]:
        async def _init() -> bool:
            config = await self._network.fetch_config(user, self._store.get_last_update_time())
            if config is None:
                return False
            self._store.set_values(config)
            self._initialized = True
            self._user = user
            return True

        return self._runtime.submit(_init())

    def get_experiment(self, user: WolvesUser, experiment_name: str) -> Experiment:
        if not self._initialized:
            self._initialized = True
            self._user = user

            async def _background_fetch() -> None:
                config = await self._network.fetch_config(user, self._store.get_last_update_time())
                if config is not None:
                    self._store.set_values(config)

            self._runtime.submit(_background_fetch())

        cfg = self._store.get_experiment(experiment_name)
        value = cfg.value if cfg else {}
        experiment_id = (cfg.experiment_id or "") if cfg else ""
        group_name = cfg.group if cfg else None

        self._log_exposure(user, experiment_name, experiment_id, group_name or "", value)
        return Experiment(
            name=experiment_name,
            value=value,
            experiment_id=experiment_id,
            group_name=group_name,
        )

    def get_experiment_for_test(self, experiment_name: str, group_name: str, user: WolvesUser | None = None) -> Experiment:
        cfg = self._store.get_experiment(experiment_name)
        experiment_id = (cfg.experiment_id or "") if cfg else ""

        exposure_user = user or self._user or WolvesUser()
        self._log_exposure(exposure_user, experiment_name, experiment_id, group_name, {})

        return Experiment(
            name=experiment_name,
            value={},
            experiment_id=experiment_id,
            group_name=group_name,
        )

    def log_event(
        self,
        user: WolvesUser,
        event_name: str,
        value: str | float | int | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        event = WolvesEvent(
            event_name=event_name,
            user=user,
            time_ms=int(time.time() * 1000),
            value=value,
            metadata=metadata,
        )
        self._logger.enqueue(event)

    def shutdown(self) -> WolvesFuture[None]:
        self._logger.stop().wait(timeout=5)
        self._runtime.submit(self._network.aclose()).wait(timeout=5)
        self._runtime.stop()
        fut: concurrent.futures.Future[None] = concurrent.futures.Future()
        fut.set_result(None)
        return WolvesFuture(fut)

    def _log_exposure(
        self,
        user: WolvesUser,
        experiment_name: str,
        experiment_id: str,
        group_name: str,
        value: dict,
    ) -> None:
        event = WolvesEvent(
            event_name="exposure",
            user=user,
            time_ms=int(time.time() * 1000),
            metadata={
                "experiment_name": experiment_name,
                "experiment_id": experiment_id,
                "group": group_name,
                "value": json.dumps(value),
            },
        )
        self._logger.enqueue(event)
