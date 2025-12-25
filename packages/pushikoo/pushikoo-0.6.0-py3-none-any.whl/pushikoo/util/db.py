import json
from sqlalchemy.types import TypeDecorator, TEXT
from pushikoo_interface import Struct


class StructField(TypeDecorator):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, Struct):
            payload = value.model_dump()
        else:
            payload = value
        return json.dumps(payload, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return Struct(json.loads(value))
        except Exception:
            try:
                return json.loads(value)
            except Exception:
                return value


class JSONField(TypeDecorator):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Use default=str so objects like UUID can be serialized
        return json.dumps(value, ensure_ascii=False, default=str)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return json.loads(value)
        except Exception:
            return value
