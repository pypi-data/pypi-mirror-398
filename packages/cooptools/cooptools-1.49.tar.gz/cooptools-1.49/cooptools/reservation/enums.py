from enum import Enum, auto

class ResultStatus(Enum):
    SUCCESS = auto()
    FAILED = auto()

class ReservationMethod(Enum):
    ALL_OR_NONE = auto()
    AS_MANY_AS_POSSIBLE = auto()
    FIRST = auto()

class ReservationResultExplanation(Enum):
    ACQUIRED = auto()
    NOT_AVAILABLE = auto()
    ALREADY_HAD = auto()

class UnReservationResultExplanation(Enum):
    RELINQUISHED = auto()
    DOESNT_OWN_RESERVATION = auto()
    NOT_RESERVED = auto()
