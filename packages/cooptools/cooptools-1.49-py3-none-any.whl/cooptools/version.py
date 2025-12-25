from dataclasses import dataclass
from typing import Dict, Tuple, List
from cooptools.common import verify

def verify_type_isVersion(other, msg):
    if type(other) == str:
        other = Version(other)

    verify(lambda: type(other) == Version, msg=msg, block=True)
    return other

@dataclass(frozen=True)
class Version:
    txt: str
    lvls: Dict[int, str] = None

    @classmethod
    def from_val(cls, val):
        return verify_type_isVersion(val, f"Unable to create [{type(cls)}] from [{type(val)}]")

    def __post_init__(self):
        super().__setattr__(f'{self.lvls=}'.split('=')[0].replace('self.', ''), {ii: val for ii, val in enumerate(self.txt.split('.'))})

    @classmethod
    def _verify_type_other(cls, other, msg):
        if type(other) == str:
            other = Version(other)

        verify(lambda: type(other) == Version, msg=msg, block=True)

    @property
    def SortedLvls(self) -> List[Tuple[int, str]]:
        lvls = [(lvl, val) for lvl, val in self.lvls.items()]
        lvls.sort(key=lambda x: x[0])
        return lvls

    def __gt__(self, other):
        other = verify_type_isVersion(other, msg=f"Unable to compare (gt) version types [{type(self)}] vs [{type(other)}]")

        for lvl, val in self.SortedLvls:
            if val > other.lvls[lvl]:
                return True

        return False

    def __lt__(self, other):
        other = verify_type_isVersion(other, msg=f"Unable to compare (lt) version types [{type(self)}] vs [{type(other)}]")

        for lvl, val in self.SortedLvls:
            if val < other.lvls[lvl]:
                return True

        return False

    def __eq__(self, other):
        other = verify_type_isVersion(other, msg=f"Unable to compare (eq) version types [{type(self)}] vs [{type(other)}]")

        for lvl, val in self.SortedLvls:
            if val != other.lvls[lvl]:
                return False

        return True

    def __ge__(self, other):
        return not self.__lt__(other)

    def __le__(self, other):
        return not self.__gt__(other)

    def __hash__(self):
        return hash(self.txt)

if __name__ == "__main__":
    vz = Version('a.1.4')
    vz2 = Version('a.1.5')

    print(vz.lvls)

    print(vz >= vz2)
    print(vz > vz2)
    print(vz2 > vz)
    print(vz2 >= vz)
