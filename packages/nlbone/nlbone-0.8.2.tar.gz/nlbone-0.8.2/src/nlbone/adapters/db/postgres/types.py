from sqlalchemy.types import BigInteger, TypeDecorator


class BaseIntegerIdType(TypeDecorator):
    """Maps BaseId subclasses <-> BIGINT transparently (Infrastructure-only)."""

    impl = BigInteger
    cache_ok = True

    def __init__(self, id_cls):
        super().__init__()
        self.id_cls = id_cls

    def process_bind_param(self, value, dialect):
        # Python -> DB
        if value is None:
            return None
        return int(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.id_cls(int(value))
