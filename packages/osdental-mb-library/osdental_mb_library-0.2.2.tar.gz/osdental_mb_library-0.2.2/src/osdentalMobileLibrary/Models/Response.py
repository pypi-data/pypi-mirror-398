from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import datetime, date
from enum import Enum
from ..Shared.Enums.Code import Code
from ..Shared.Enums.Message import Message


def deep_serialize(obj):

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, Enum):
        return obj.value if hasattr(obj, "value") else str(obj)

    if is_dataclass(obj):
        return {k: deep_serialize(v) for k, v in asdict(obj).items()}

    if isinstance(obj, dict):
        return {k: deep_serialize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [deep_serialize(item) for item in obj]

    return obj


@dataclass
class Response:
    status: str = field(default=Code.PROCESS_SUCCESS_CODE)
    message: str = field(default=Message.PROCESS_SUCCESS_MSG)
    data: str = field(default=None)

    def __post_init__(self):
        if isinstance(self.status, Enum):
            self.status = str(self.status)
        if isinstance(self.message, Enum):
            self.message = str(self.message)

    def send(self):
        return {
            "status": self.status,
            "message": self.message,
            "data": deep_serialize(self.data),
        }
