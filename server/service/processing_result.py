from enum import IntEnum, auto


class ProcessingResult(IntEnum):
    SUCCESS_ACCEPTED = auto()
    SUCCESS_CREATED = auto()
    SUCCESS_RETRIEVED = auto()
    SUCCESS_UPDATED = auto()
    SUCCESS_DELETED = auto()

    ERROR_NOT_FOUND = auto()
    ERROR_SERVICE_UNAVAILABLE = auto()
    ERROR_ALREADY_EXISTS = auto()
    ERROR_BAD_REQUEST = auto()
    ERROR_CREATING_FAILED = auto()
    ERROR_UPDATING_FAILED = auto()
    ERROR_UNPROCESSABLE_ENTITY = auto()
    ERROR_NOT_IMPLEMENTED = auto()
    ERROR_INTERNAL_SERVER_ERROR = auto()
    ERROR_FORBIDDEN = auto()
