import uuid


class Cacheable:
    _id: str

    def __init__(self) -> None:
        self._id = uuid.uuid4().hex

    def _update_id(self) -> None:
        self._id = uuid.uuid4().hex

    @property
    def uid(self) -> str:
        return self._id
