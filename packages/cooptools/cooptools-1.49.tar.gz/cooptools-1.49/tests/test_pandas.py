import unittest
from cooptools.pandasHelpers import convert_pandas_data_columns_to_type, clean_a_dataframe, PandasMissingColumnsException, PandasFillColumnTypeException
import pandas as pd
import numpy as np
import datetime

class Test_Pandas(unittest.TestCase):

    def test__convert_pandas_data_columns_to_type__df_is_none(self):
        df = None
        column_definitions = {"a": int, "b": int, "c": int}

        converted = convert_pandas_data_columns_to_type(df, column_type_definition=column_definitions)

        self.assertEqual(converted, None)

    def test__convert_pandas_data_columns_to_type__df_is_empty(self):
        df = pd.DataFrame()
        column_definitions = {"a": int, "b": int, "c": int}

        converted = convert_pandas_data_columns_to_type(df, column_type_definition=column_definitions)

        self.assertEqual(converted.equals(df), True)

    def test__convert_pandas_data_columns_to_type__missing_columns(self):
        df = pd.DataFrame(data=[{'a': 1, 'b': 2}])
        column_definitions = {"a": int, "b": int, "c": int}

        converted = convert_pandas_data_columns_to_type(df, column_type_definition=column_definitions)
        self.assertListEqual([x for x in converted.columns], ['a', 'b'])

    def test__convert_pandas_data_columns_to_type__too_many_columns(self):
        df = pd.DataFrame(data=[{'a': 1, 'b': 2, 'c':3, 'd':4}])
        column_definitions = {"a": int, "b": int, "c": int}

        converted = convert_pandas_data_columns_to_type(df, column_type_definition=column_definitions)

        self.assertListEqual([x for x in converted.columns], ['a', 'b', 'c', 'd'])

    def test__convert_pandas_data_columns_to_type__int_dirty_values(self):
        df = pd.read_csv('./tests/testdata/ints_dirty.csv')
        column_definitions = {"my_int": int}

        self.assertRaises(ValueError, lambda: convert_pandas_data_columns_to_type(df, column_type_definition=column_definitions))

    def test__convert_pandas_data_columns_to_type__int_clean_values(self):
        df = pd.read_csv('./tests/testdata/ints_clean.csv')
        column_definitions = {"my_int": np.int64}

        converted = convert_pandas_data_columns_to_type(df, column_type_definition=column_definitions)


        self.assertIn(converted.dtypes['my_int'], [np.int8, np.int32, np.int64])
        # self.assertEqual(converted.dtypes['my_int'], np.int64)


    def test__clean_a_dataframe__too_many_columns(self):
        df = pd.read_csv('./tests/testdata/dummy_data_clean.csv')
        column_definitions = {"my_clean_int": np.int64, "my_clean_str": str}

        converted = clean_a_dataframe(df, column_type_definition=column_definitions)

        self.assertEqual(converted.dtypes['my_clean_int'], np.int64)
        self.assertEqual(converted.dtypes['my_clean_str'], object)
        self.assertEqual([x for x in converted.columns], ['my_clean_int', 'my_clean_str'])

    def test__clean_a_dataframe__not_enough_columns__allow_partial__dont_fill_missing(self):
        df = pd.read_csv('./tests/testdata/dummy_data_clean.csv')
        column_definitions = {"my_clean_int": int,
                              "my_clean_str": str,
                              "my_clean_date": datetime.date,
                              "my_missing_column": np.int64}

        converted = clean_a_dataframe(df, column_type_definition=column_definitions, allow_partial_columnset=True, fill_missing=False)

        self.assertIn(converted.dtypes['my_clean_int'], [np.int8, np.int32, np.int64])
        self.assertEqual(converted.dtypes['my_clean_str'], object)
        self.assertEqual([x for x in converted.columns], ['my_clean_int', 'my_clean_str','my_clean_date'])

    def test__clean_a_dataframe__not_enough_columns__allow_partial__fill_missing(self):
        df = pd.read_csv('./tests/testdata/dummy_data_clean.csv')
        column_definitions = {"my_clean_int": int,
                              "my_clean_str": str,
                              "my_clean_date": datetime.date,
                              "my_missing_column": str}

        converted = clean_a_dataframe(df, column_type_definition=column_definitions, allow_partial_columnset=True, fill_missing=True)

        self.assertIn(converted.dtypes['my_clean_int'], [np.int8, np.int32, np.int64])
        self.assertEqual(converted.dtypes['my_clean_str'], object)
        self.assertEqual([x for x in converted.columns], ['my_clean_int', 'my_clean_str', 'my_clean_date', 'my_missing_column'])


    def test__clean_a_dataframe__not_enough_columns__dont_allow_partial(self):
        df = pd.read_csv('./tests/testdata/dummy_data_clean.csv')
        column_definitions = {"my_clean_int": np.int64, "my_clean_str": str, "my_clean_date": str,
                              "my_missing_column": np.int64}

        self.assertRaises(PandasMissingColumnsException, lambda: clean_a_dataframe(df, column_type_definition=column_definitions, allow_partial_columnset=False))

    def test__clean_a_dataframe__not_enough_columns__allow_partial__fill_missing__invalid_fill_type(self):
        df = pd.read_csv('./tests/testdata/dummy_data_clean.csv')
        column_definitions = {"my_clean_int": int,
                              "my_clean_str": str,
                              "my_clean_date": datetime.date,
                              "my_missing_column": int}

        self.assertRaises(PandasFillColumnTypeException, lambda: clean_a_dataframe(df, column_type_definition=column_definitions, allow_partial_columnset=True, fill_missing=True))

    def test__clean_a_dataframe__not_case_sensititve__matching_columns(self):
        df = pd.read_csv('./tests/testdata/dummy_data_clean.csv')
        column_definitions = {"My_Clean_Int": int,
                              "My_cLean_stR": str,
                              "my_clean_date": datetime.date}

        df = clean_a_dataframe(df,
                               column_type_definition=column_definitions,
                               allow_partial_columnset=False,
                               fill_missing=False)

        self.assertEqual(list(df.columns), list(column_definitions.keys()))


    def test__convert_pandas_data_columns_to_type__currency_mixed_values(self):
        df = pd.read_csv('./tests/testdata/currency.csv')
        column_definitions = {"my_currency": float}

        converted = convert_pandas_data_columns_to_type(df, column_type_definition=column_definitions)


        self.assertIn(converted.dtypes['my_currency'], [float])
