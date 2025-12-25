import unittest
from cooptools.printing import pretty_print_dataframe, pretty_print_list_of_list
import random as rnd
import pandas as pd

class Test_Printing(unittest.TestCase):

    def test__pretty_print_dataframe(self):
        columns = 10
        rows = 100

        lst_o_lst = [[rnd.randint(0, 100) for ii in range(columns)] for jj in range(rows)]
        df = pd.DataFrame(lst_o_lst)

        try:
            pretty_print_dataframe(df)
        except Exception as e:
            self.fail(f"Print Raised unexpectedly: {e}")


    def test__pretty_print_list_of_list(self):
        columns = 10
        rows = 100

        lst_o_lst = [[rnd.randint(0, 100) for ii in range(columns)] for jj in range(rows)]

        try:
            pretty_print_list_of_list(lst_o_lst)
        except Exception as e:
            self.fail(f"Print Raised unexpectedly: {e}")