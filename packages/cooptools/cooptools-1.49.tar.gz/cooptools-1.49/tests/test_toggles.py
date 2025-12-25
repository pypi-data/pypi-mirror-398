import unittest
from cooptools.toggles import Toggleable, EnumToggleable, IntegerRangeToggleable, BooleanToggleable
from enum import Enum


class test_toggles(unittest.TestCase):

    def test__Toggleable_ToggleThroughValues(self):
        lst = ['Car', 2, 'Dog', '100']

        toggle = Toggleable(lst)

        assert toggle.value == lst[0]
        toggle.toggle()
        assert toggle.value == lst[1]
        toggle.toggle()
        assert toggle.value == lst[2]
        toggle.toggle()
        assert toggle.value == lst[3]
        toggle.toggle()
        assert toggle.value == lst[0]


    def test__EnumToggleable__ToggleThroughEnum(self):
        class Dummy(Enum):
            A = 1,
            B = 2,
            C = 3

        toggle = EnumToggleable(Dummy)

        assert toggle.value == Dummy.A
        toggle.toggle()
        assert toggle.value == Dummy.B
        toggle.toggle()
        assert toggle.value == Dummy.C
        toggle.toggle()
        assert toggle.value == Dummy.A

    def test__IntegerRangeToggleable_ToggleThroughValues(self):
        toggle = IntegerRangeToggleable(10, 15)

        assert toggle.value == 10
        toggle.toggle()
        assert toggle.value == 11
        toggle.toggle()
        assert toggle.value == 12
        toggle.toggle()
        assert toggle.value == 13
        toggle.toggle()
        assert toggle.value == 14
        toggle.toggle()
        assert toggle.value == 15
        toggle.toggle()
        assert toggle.value == 10

    def test__BooleanToggleable_ToggleThroughValues(self):
        toggle = BooleanToggleable(default=False)

        assert toggle.value == False
        toggle.toggle()
        assert toggle.value == True
        toggle.toggle()
        assert toggle.value == False