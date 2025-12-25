import unittest
from unittest.mock import Mock, MagicMock, patch
from cooptools.cli.CliAtomicUserInteraction import CliAtomicUserInteraction
import pandas as pd
import numpy as np
from cooptools.cli.fileContentReturn import FileContentReturn

class Test_CliAtomicUserInteraction(unittest.TestCase):

    @patch('pandas.read_csv')
    @patch('cooptools.cli.CliAtomicUserInteraction.CliAtomicUserInteraction.request_open_filepath')
    def test__request_data_from_csv_with_specified_columns__no_file_selected(self,
                                                                             mock_request_open_filepath,
                                                                             mock_pandas_read_csv):
        ui = CliAtomicUserInteraction()

        mock_request_open_filepath.return_value = None

        columns = {
            "test1": str,
            "test2": str,
            "test3": str
        }
        resp = ui.request_data_from_csv_with_specified_columns(column_type_definition=columns)

        self.assertIsNone(resp.data)
        self.assertIsNotNone(resp.error)
        self.assertFalse(mock_pandas_read_csv.called)

    @patch('pandas.read_csv')
    @patch('cooptools.cli.CliAtomicUserInteraction.CliAtomicUserInteraction.request_open_filepath')
    def test__request_data_from_csv_with_specified_columns__no_valid_encryption(self,
                                                                             mock_request_open_filepath,
                                                                             mock_pandas_read_csv):
        ui = CliAtomicUserInteraction()

        mock_request_open_filepath.return_value = 'GoodReturnValue'
        mock_pandas_read_csv.side_effect = [Exception(), Exception(), Exception()]
        columns = {
            "test1": str,
            "test2": str,
            "test3": str
        }
        resp = ui.request_data_from_csv_with_specified_columns(column_type_definition=columns)

        self.assertIsNone(resp.data)
        self.assertIsNotNone(resp.error)
        self.assertEqual(mock_pandas_read_csv.call_count, 3)

    @patch('pandas.read_csv')
    @patch('cooptools.cli.CliAtomicUserInteraction.CliAtomicUserInteraction.request_open_filepath')
    def test__request_data_from_csv_with_specified_columns__no_valid_encryption(self,
                                                                             mock_request_open_filepath,
                                                                             mock_pandas_read_csv):
        ui = CliAtomicUserInteraction()

        mock_request_open_filepath.return_value = 'GoodReturnValue'
        mock_pandas_read_csv.side_effect = [Exception(), Exception(), Exception()]
        columns = {
            "test1": str,
            "test2": str,
            "test3": str
        }
        resp = ui.request_data_from_csv_with_specified_columns(column_type_definition=columns)

        self.assertIsNone(resp.data)
        self.assertEqual(mock_pandas_read_csv.call_count, 3)

    @patch('pandas.read_csv')
    @patch('cooptools.cli.CliAtomicUserInteraction.CliAtomicUserInteraction.request_open_filepath')
    def test__request_data_from_csv_with_specified_columns__valid_return(self,
                                                                             mock_request_open_filepath,
                                                                             mock_pandas_read_csv):
        ui = CliAtomicUserInteraction()
        columns = {
            "test1": str,
            "test2": str,
            "test3": str
        }
        good_file_path = 'tests/testdata/data_ui.csv'


        mock_request_open_filepath.return_value = good_file_path
        good_df = pd.DataFrame(columns=list(columns.keys()))
        good_return = FileContentReturn(file_path=good_file_path, data=good_df)
        mock_pandas_read_csv.side_effect = [Exception(), Exception(), good_df]

        resp = ui.request_data_from_csv_with_specified_columns(column_type_definition=columns)

        self.assertTrue(good_return.file_path == resp.file_path)
        self.assertTrue(good_return.data.equals(resp.data))
        self.assertEqual(mock_pandas_read_csv.call_count, 3)

    @patch('tkinter.filedialog.askdirectory')
    def test__request_directory__no_directory_selected(self,
                                                     mock_tkinter_askdirectory):
        ui = CliAtomicUserInteraction()

        mock_tkinter_askdirectory.side_effect = [None]

        resp = ui.request_directory()

        self.assertIsNone(resp)

    @patch('tkinter.filedialog.askdirectory')
    def test__request_directory__good_directory_selected(self,
                                                       mock_tkinter_askdirectory):
        ui = CliAtomicUserInteraction()

        good_return = 'GoodReturnValue'
        mock_tkinter_askdirectory.side_effect = [good_return]

        resp = ui.request_directory()

        self.assertEqual(good_return, resp)


    @patch('tkinter.filedialog.asksaveasfilename')
    def test__request_save_filepath__no_directory_selected(self,
                                                     mock_tkinter_asksaveasfilename):
        ui = CliAtomicUserInteraction()

        mock_tkinter_asksaveasfilename.side_effect = [None]

        resp = ui.request_save_filepath()

        self.assertIsNone(resp)

    @patch('tkinter.filedialog.asksaveasfilename')
    def test__request_save_filepath__good_directory_selected(self,
                                                       mock_tkinter_asksaveasfilename):
        ui = CliAtomicUserInteraction()

        good_return = 'GoodReturnValue'
        mock_tkinter_asksaveasfilename.side_effect = [good_return]

        resp = ui.request_save_filepath()

        self.assertEqual(good_return, resp)

    @patch('builtins.input')
    def test__request_from_df__additional_options__select_in_df(self,
                                                  mock_input):
        #arrange
        add_options = ['T1', 'T2', 'T3']
        df_size = 10
        df = pd.DataFrame({'A': [x for x in range(df_size)]},columns=['A'])
        mock_input.side_effect = [str(df_size-1)]

        #act
        ret = CliAtomicUserInteraction.request_index_from_df(df, additional_options=add_options)

        #assert
        self.assertEqual(mock_input.call_count, 1)
        self.assertEqual(ret, df_size - 1)

    @patch('builtins.input')
    def test__request_from_df__additional_options__select_in_add_options(self,
                                                  mock_input):
        #arrange
        add_options = ['T1', 'T2', 'T3']
        df_size = 10
        df = pd.DataFrame({'A': [x for x in range(df_size)]},columns=['A'])
        mock_input.side_effect = [str(df_size)]

        #act
        ret = CliAtomicUserInteraction.request_index_from_df(df, additional_options=add_options)

        #assert
        self.assertEqual(mock_input.call_count, 1)
        self.assertEqual(ret, 'T1')

    @patch('builtins.input')
    def test__request_from_df__additional_options__ind_to_high(self,
                                                  mock_input):
        #arrange
        add_options = ['T1', 'T2', 'T3']
        df_size = 10
        df = pd.DataFrame({'A': [x for x in range(df_size)]},columns=['A'])
        mock_input.side_effect = [str(df_size + len(add_options)), 'X']

        #act
        ret = CliAtomicUserInteraction.request_index_from_df(df, additional_options=add_options)

        #assert
        self.assertEqual(mock_input.call_count, 2)
        self.assertEqual(ret, None)