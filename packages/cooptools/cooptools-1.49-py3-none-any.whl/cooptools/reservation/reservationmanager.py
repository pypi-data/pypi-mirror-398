import logging
from typing import Hashable, List, Dict
from threading import RLock
import cooptools.reservation.enums as enums
import cooptools.reservation.dcs as rdcs

logger = logging.getLogger('cooplock')

class ReservationManager():
    def __init__(self):
        self._resource_reservations = {}
        self._lock = RLock()

    @property
    def ActiveReservations(self):
        return {key: value for key, value in self._resource_reservations.items() if value}

    @property
    def ReservationHolders(self):
        holders = {}
        for k, v in self.ActiveReservations.items():
            holders.setdefault(v, []).append(k)
        return holders

    def register_resources(self, resources: List[Hashable]):
        for x in resources:
            self._resource_reservations.setdefault(x, None)

    def reserve_resource(self, resource: Hashable, requester: Hashable) -> rdcs.ReservationResult:
        with self._lock:
            if self._resource_reservations.get(resource, None) is None:
                self._resource_reservations[resource] = requester
                exp = enums.ReservationResultExplanation.ACQUIRED
                result = enums.ResultStatus.SUCCESS
            elif self._resource_reservations.get(resource, None) == requester:
                exp = enums.ReservationResultExplanation.ALREADY_HAD
                result = enums.ResultStatus.SUCCESS
            else:
                exp = enums.ReservationResultExplanation.NOT_AVAILABLE
                result = enums.ResultStatus.FAILED

            ret = rdcs.ReservationResult(
                requested=resource,
                requester=requester,
                explanation=exp,
                result=result
            )
            logger.debug(
                f"Reserve for resource: {resource} by {requester} -> Result:{ret}")
            return ret

    def unreserve_resources(self, resources: List[Hashable], requester: Hashable) -> List[rdcs.ReservationResult]:
        return [self._unreserve_resource(x, requester) for x in resources]

    def _unreserve_resource(self, resource: Hashable, requester: Hashable) -> rdcs.ReservationResult:
        with self._lock:
            if self._resource_reservations.get(resource, None) is None:
                exp = enums.UnReservationResultExplanation.NOT_RESERVED
                res = enums.ResultStatus.SUCCESS
            elif self._resource_reservations.get(resource, None) == requester:
                self._resource_reservations[resource] = None
                exp = enums.UnReservationResultExplanation.RELINQUISHED
                res = enums.ResultStatus.SUCCESS
            elif self._resource_reservations.get(resource, None) is not None:
                exp = enums.UnReservationResultExplanation.DOESNT_OWN_RESERVATION
                res = enums.ResultStatus.FAILED
            else:
                raise RuntimeError(f"Unknown situation for resource {resource} unreserve request for {requester}, state: {self._resource_reservations.get(resource, None)}")

            ret = rdcs.ReservationResult(
                requested=resource,
                result=res,
                requester=requester,
                explanation=exp
            )
            logger.debug(f"Un-reserve for resource: {resource} by {requester} -> Result:{ret}")
            return ret

    def _handle_transaction(self, transaction: rdcs.ReservationTransaction) -> rdcs.ReservationTransactionResult:
        with self._lock:
            logger.debug(f"Starting Transaction {transaction}")
            results = [self.reserve_resource(resource=x,
                                             requester=transaction.requester)
                       for x in transaction.requested]

            success = [x for x in results if x.result == enums.ResultStatus.SUCCESS]
            failed = [x for x in results if x.result == enums.ResultStatus.FAILED]


            to_unreserve = []

            if transaction.method == enums.ReservationMethod.FIRST and len(success) > 0:

                ret = rdcs.ReservationTransactionResult(
                    transaction=transaction,
                    result=enums.ResultStatus.SUCCESS,
                    available=[x.requested for x in success],
                    unavailable=[x.requested for x in failed],
                    reserved=[success[0].requested]
                )
                # unreserve all but the first
                to_unreserve = success[1:]
            elif transaction.method == enums.ReservationMethod.FIRST and len(success) == 0:
                ret = rdcs.ReservationTransactionResult(
                    transaction=transaction,
                    result=enums.ResultStatus.FAILED,
                    available=[x.requested for x in success],
                    unavailable=[x.requested for x in failed],
                    reserved=[]
                )

            elif transaction.method == enums.ReservationMethod.ALL_OR_NONE and len(failed) > 0:
                ret = rdcs.ReservationTransactionResult(
                    transaction=transaction,
                    result=enums.ResultStatus.FAILED,
                    available=[x.requested for x in success],
                    unavailable=[x.requested for x in failed],
                    reserved=[]
                )

                # unreserve all but the first
                to_unreserve = success

            elif transaction.method == enums.ReservationMethod.ALL_OR_NONE and len(failed) == 0:
                ret = rdcs.ReservationTransactionResult(
                    transaction=transaction,
                    result=enums.ResultStatus.SUCCESS,
                    available=[x.requested for x in success],
                    unavailable=[x.requested for x in failed],
                    reserved=[x.requested for x in success]
                )

            elif transaction.method == enums.ReservationMethod.AS_MANY_AS_POSSIBLE:
                ret = rdcs.ReservationTransactionResult(
                    transaction=transaction,
                    result=enums.ResultStatus.FAILED,
                    available=[x.requested for x in success],
                    unavailable=[x.requested for x in failed],
                    reserved=[x.requested for x in success]
                )

            else:
                raise RuntimeError(f"Unhandled workflow for {transaction.method}, success: {success}, fail: {failed}")

            # handle unreserving
            unreserves = [self._unreserve_resource(x.requested, x.requester) for x in to_unreserve if
                          x.explanation == enums.ReservationResultExplanation.ACQUIRED]

            # raise if couldnt unreserve all
            if not all(x.result == enums.ResultStatus.SUCCESS for x in unreserves):
                raise RuntimeError(f"All the unreserves did not happen successfully: {unreserves}")

            logger.debug(f"Transaction {transaction} finished with {ret}")
            return ret

    def handle_reservation_transactions(self, transactions: List[rdcs.ReservationTransaction]) -> List[rdcs.ReservationTransactionResult]:
        results = [self._handle_transaction(x) for x in transactions]
        return results

    def check_has_reservations(self,
                               requester: Hashable,
                               resources: List[Hashable],
                               check_any: bool=None,
                               at_least: int = None) -> bool:
        if check_any == True:
            return any([self._resource_reservations.get(x, None) == requester for x in resources])

        if at_least is not None:
            return len([self._resource_reservations.get(x, None) == requester for x in resources]) >= at_least

        return all([self._resource_reservations.get(x, None) == requester for x in resources])

    def check_if_reserved(self, resources: List[Hashable]) -> Dict[Hashable, bool]:
        return {x: self._resource_reservations.get(x, None) is not None for x in resources}

    def requesters_reservations(self, requester: Hashable) -> List[Hashable]:
        return self.ReservationHolders.get(requester, [])

    def reset(self):
        with self._lock:
            self._resource_reservations = {}

if __name__ == "__main__":
    from pprint import pprint
    logging.basicConfig(level=logging.DEBUG)
    locker = ReservationManager()
    
    bloc_dict = {
        'a': ['b', 'c', 'd'],
        'b': ['a', 'd', 'f'],
        'c': ['g'],
        'd': ['a', 'f'],
        'e': ['f'],
        'g': ['d']
    }

    def reserve_it_transaction(requester, it, bloc_dict) -> rdcs.ReservationTransaction:
        to_reserve = [it] + bloc_dict.get(it, [])
        return rdcs.ReservationTransaction(to_reserve, requester, method=enums.ReservationMethod.ALL_OR_NONE)

    def test_1():
        t_results = locker.handle_reservation_transactions([reserve_it_transaction('me', 'a', bloc_dict)])

        pprint(locker.ActiveReservations)
        pprint(locker.ReservationHolders)
        pprint(locker.requesters_reservations('me'))

        [locker.unreserve_resources(x.reserved, x.transaction.requester) for x in t_results]
        print(locker.ActiveReservations)
        pprint(locker.ReservationHolders)
        pprint(locker.requesters_reservations('me'))

    test_1()
