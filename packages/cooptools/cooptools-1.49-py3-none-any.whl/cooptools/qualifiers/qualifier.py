from dataclasses import dataclass, field
import re
from typing import Iterable, Protocol, Callable, Optional, Tuple, Dict, Any, List
from cooptools import typeProviders as tp
from cooptools.protocols import IdentifiableProtocol, UniqueIdentifier
import cooptools.geometry_utils.vector_utils as vec

@dataclass(frozen=True, slots=True)
class QualifierResponse:
    result: bool
    failure_reasons: List[str] = field(default_factory=list)

    def __bool__(self):
        return self.result

class QualifierProtocol(Protocol):
    def qualify(self, values: Iterable) -> Dict[Any, QualifierResponse]:
        pass

@dataclass(frozen=True, slots=True)
class WhiteBlackListQualifier(QualifierProtocol):
    white_list: Iterable = None
    black_list: Iterable = None

    def qualify(self, values: Iterable) -> Dict[Any, QualifierResponse]:
        ret = {}

        for value in values:
            failure_reasons = []
            val = True

            if self.white_list and value not in self.white_list:
                failure_reasons += [f"value {value} not in white_list {self.white_list}"]
                val = False

            if self.black_list and value in self.black_list:
                failure_reasons += [f"value {value} in black_list {self.black_list}"]
                val = False

            ret[value] = QualifierResponse(result=val, failure_reasons=failure_reasons)
        return ret

    def qualify_many(self,
                     values: Iterable,
                     all_in_white: bool = False,
                     any_in_white: bool = False,
                     none_in_black: bool = False,
                     at_least_one_not_in_black: bool = False) -> QualifierResponse:

        ret = True
        failure_reasons = []
        if all_in_white and not all(x in self.white_list for x in values):
            failure_reasons += [f"not all values {values} are in white_list {self.white_list}"]
            ret = False

        if any_in_white and not any(x in self.white_list for x in values):
            failure_reasons += [f"not any values {values} are in white_list {self.white_list}"]
            ret = False

        if none_in_black and any(x in self.black_list for x in values):
            present = [x for x in values if x in self.black_list]
            failure_reasons += [f"values {present} are in black_list {self.black_list}"]
            ret = False

        if at_least_one_not_in_black and all(x in self.black_list for x in values):
            failure_reasons += [f"all values {values} are in black_list {self.black_list}"]
            ret = False

        return QualifierResponse(result=ret, failure_reasons=failure_reasons)

@dataclass(frozen=True, slots=True)
class WhiteBlackManyListQualifier(QualifierProtocol):
    white_black_list_qualifier: WhiteBlackListQualifier = field(default_factory=WhiteBlackListQualifier)
    all_in_white: bool = False
    any_in_white: bool = False
    none_in_black: bool = False
    at_least_one_not_in_black: bool = False

    def qualify(self, values: Iterable[Iterable]) -> Dict[Any, QualifierResponse]:
        ret = {}

        for idx, lst in enumerate(values):
            ret[idx] = self.white_black_list_qualifier.qualify_many(
                values=lst,
                all_in_white=self.all_in_white,
                any_in_white=self.any_in_white,
                none_in_black=self.none_in_black,
                at_least_one_not_in_black=self.at_least_one_not_in_black
            )

        return ret

@dataclass(frozen=True, slots=True)
class PatternMatchQualifier(QualifierProtocol):
    id: str = None
    regex: str = None
    regex_all: Iterable[str] = None
    regex_any: Iterable[str] = None
    white_list_black_list_qualifier: WhiteBlackListQualifier = None

    def __post_init__(self):
        if self.regex is not None and self.regex_all is None:
            object.__setattr__(self, 'regex_all', [self.regex])
        elif self.regex is not None and self.regex_all is not None:
            object.__setattr__(self, 'regex_all', list(self.regex_all) + [self.regex])

    def qualify(self, values: Iterable[str]) -> Dict[str, QualifierResponse]:
        ret = {}
        for value in values:
            val = True

            failure_reasons = []

            if self.id is not None and value != self.id:
                failure_reasons += [
                    f"value {value} does not match the required id: {self.id}"]
                val = False

            if self.regex_all is not None and not all(re.match(pattern, value) for pattern in self.regex_all):
                mismatches = [x for x in self.regex_all if not re.match(x, value)]
                failure_reasons += [f"value {value} does not match the following regex patterns in regex_all: {mismatches}"]
                val = False

            if self.regex_any is not None and not any(re.match(pattern, value) for pattern in self.regex_any):
                failure_reasons += [f"value {value} does not match any of the regex patterns in regex_any: {self.regex_any}"]
                val = False

            if self.white_list_black_list_qualifier is not None:
                qualify = self.white_list_black_list_qualifier.qualify([value])[value]
                failure_reasons += qualify.failure_reasons
                val = val and qualify.result

            ret[value] = QualifierResponse(result=val, failure_reasons=failure_reasons)

        return ret

@dataclass(frozen=True, slots=True)
class DimensionQualifier(QualifierProtocol):
    max_dims: Optional[vec.FloatVec] = None
    min_dims: Optional[vec.FloatVec] = None

    def qualify(self, dimension_sets: vec.IterVec):
        ret = {}
        for idx, dimension_set in enumerate(dimension_sets):
            val = True
            failure_reasons = []

            # Disqualify on Max Dims
            if self.max_dims is not None and \
                    not all(list(dimension_set)[ii] <= self.max_dims[ii] for ii in range(len(self.max_dims))):
                vec.verify_len_match(self.max_dims,
                                     dimension_set,
                                     block=True)


                failure_reasons += [
                    f"value {dimension_set} is not less than the defined max_dims: {self.max_dims}"]
                val = False

            # Disqualify on Min Dims
            if self.min_dims is not None and \
                    not all(list(dimension_set)[ii] >= list(self.max_dims)[ii] for ii in range(len(self.min_dims))):
                vec.verify_len_match(self.min_dims,
                                     dimension_set,
                                     block=True)
                failure_reasons += [
                    f"value {dimension_set} is not greater than the defined min_dims: {self.min_dims}"]
                val = False

            ret[idx] = QualifierResponse(result=val, failure_reasons=failure_reasons)
        return ret

@dataclass(frozen=True, slots=True)
class IdDimQualifier(QualifierProtocol):
    id_pattern: Optional[PatternMatchQualifier] = None
    dim_qualifer: Optional[DimensionQualifier] = None

    def qualify(self,
                id_dim_sets: Iterable[Tuple[UniqueIdentifier, vec.FloatVec]]) -> Dict[
        UniqueIdentifier, QualifierResponse]:

        id_quals = self.id_pattern.qualify([x[0] for x in id_dim_sets])
        dim_quals = self.dim_qualifer.qualify([x[1] for x in id_dim_sets])

        return {
            x[0]: QualifierResponse(result=all([id_quals[x[0]].result, dim_quals[idx].result]),
                                    failure_reasons=id_quals[x[0]].failure_reasons + dim_quals[idx].failure_reasons)
            for idx, x in enumerate(id_dim_sets)
        }


QualifierProvider = Iterable[QualifierProtocol] | Callable[[], Iterable[QualifierProtocol]]

def resolve_qualifier_provider(qp: QualifierProvider):
    return tp.resolve(qp)


if __name__ == "__main__":
    def test_001():
        print(pat:= re.compile('A'))
        print(pat.match('B1'))
        print(bool(re.match('A', "B1")))

    test_001()
