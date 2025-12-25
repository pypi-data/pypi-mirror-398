from typing import Generic, TypeVar

import threading

from loguru import logger
from pydantic import BaseModel, ValidationError

from pushikoo.db import Config as ConfigDB, get_session

TCONFIG = TypeVar("TCONFIG", bound=BaseModel)


class ConfigService(Generic[TCONFIG]):
    _locks: dict[str, threading.Lock] = {}

    def __init__(self, id_: str, model_type: type[TCONFIG] = None):
        self.id = id_
        self.model: type[BaseModel] = model_type

    @classmethod
    def _get_lock(cls, key: str) -> threading.Lock:
        return cls._locks.setdefault(key, threading.Lock())

    def get(self) -> TCONFIG:
        def struct_config():
            try:
                return self.model()
            except Exception:
                return None

        lock = self._get_lock(self.id)
        with lock:
            with get_session() as session:
                row = session.get(ConfigDB, self.id)
                if row and row.value is not None:
                    try:
                        return self.model.model_validate(row.value)
                    except ValidationError:
                        logger.warning(f"Invalid config for {self.id}")
                        session.delete(row)
                        session.commit()
                        return struct_config()

                return struct_config()

    def set(self, config: TCONFIG):
        data = config.model_dump()
        lock = self._get_lock(self.id)
        with lock:
            with get_session() as session:
                row = session.get(ConfigDB, self.id)
                if row is None:
                    row = ConfigDB(key=self.id, value=data)
                else:
                    row.value = data
                session.add(row)
                session.commit()
        logger.info(f"Updated config: {self.id}")

    def delete(self) -> bool:
        lock = self._get_lock(self.id)
        with lock:
            with get_session() as session:
                row = session.get(ConfigDB, self.id)
                if row is not None:
                    session.delete(row)
                    session.commit()
                    logger.info(f"Deleted config: {self.id}")
                    return True
                return False
