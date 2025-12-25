from typing import Iterable

def increasing(lst: Iterable, strict: bool = True) -> bool:

    if strict:
        return all(x<y for x, y in zip(lst, lst[1:]))
    else:
        return all(x<=y for x, y in zip(lst, lst[1:]))

def decreasing(lst: Iterable, strict: bool = True) -> bool:

    if strict:
        return all(x>y for x, y in zip(lst, lst[1:]))
    else:
        return all(x>=y for x, y in zip(lst, lst[1:]))

def alternating_positivity(lst: Iterable) -> bool:
    return all((x>0) != (y>0) for x, y in zip(lst, lst[1:]))

def change_within_delta(lst: Iterable, delta: float, inclusive: bool = True) -> bool:
    if inclusive:
        return all(abs(x-y) <= delta for x, y in zip(lst, lst[1:]))
    else:
        return all(abs(x - y) < delta for x, y in zip(lst, lst[1:]))

def change_outside_delta(lst: Iterable, delta: float, inclusive: bool = True) -> bool:
    if inclusive:
        return all(abs(x-y) >= delta for x, y in zip(lst, lst[1:]))
    else:
        return all(abs(x - y) > delta for x, y in zip(lst, lst[1:]))

def monotonic(lst: Iterable, strict: bool = False) -> bool:
    return increasing(lst, strict) or decreasing(lst, strict)


if __name__ == "__main__":
    inc_lst = [1, 2, 3]
    dec_lst = [3, 2, 1]
    alt_lst = [1, -4, 2, -1]

    print(increasing(inc_lst))
    print(increasing(dec_lst))
    print(decreasing(inc_lst))
    print(decreasing(dec_lst))
    print(monotonic(inc_lst))
    print(alternating_positivity(inc_lst))
    print(alternating_positivity(alt_lst))