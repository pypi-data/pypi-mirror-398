from dataclasses import dataclass, field
import cooptools.reservation.enums as enums
from typing import Hashable, List
import uuid

@dataclass(frozen=True, slots=True)
class ReservationResult:
    requested: Hashable
    requester: Hashable
    explanation: enums.ReservationResultExplanation | enums.UnReservationResultExplanation
    result: enums.ResultStatus
    token: uuid.UUID = field(default_factory=uuid.uuid4, init=False)

@dataclass(frozen=True, slots=True)
class ReservationTransaction:
    requested: List[Hashable]
    requester: Hashable
    method: enums.ReservationMethod

@dataclass(frozen=True, slots=True)
class ReservationTransactionResult:
    result: enums.ResultStatus
    available: List[Hashable]
    unavailable: List[Hashable]
    transaction: ReservationTransaction
    reserved: List[Hashable]


