import time
from enum import Enum
from dateutil import parser
import datetime
from typing import Dict, List, Generic, TypeVar, Tuple, Optional, Callable, Union
import tkinter
import tkinter.filedialog as fd
from pprint import pprint
import pandas as pd
from cooptools.pandasHelpers import clean_a_dataframe
import cooptools.typevalidation as tv
import logging
from cooptools.cli.fileContentReturn import FileContentReturn
import cooptools.geometry_utils.vector_utils as vec
from cooptools import pandasHelpers as ph

T = TypeVar('T')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

StringProvider = Union[str, Callable[[], str]]
StringByIndexProvider = Union[str, Callable[[int], str]]
IntProvider = Union[int, Callable[[], int]]
FloatProvider = Union[float, Callable[[], float]]


def _resolve(
        provider,
        *args
):
    if callable(provider):
        return provider(*args)

    return provider


def resolve_string_provider(
        string_provider: StringProvider
) -> str:
    return _resolve(string_provider)


def resolve_string_by_index_provider(
        string_by_index_provider: StringByIndexProvider,
        index: int
) -> str:
    return _resolve(string_by_index_provider,
                    index)


def resolve_prompt_text(prompt: StringProvider = None,
                        default: str = None):
    if prompt is None:
        prompt = default
    if prompt is None:
        prompt = ''

    prompt = resolve_string_provider(prompt)
    prompt = prompt.replace(":", " ")

    return prompt


class CliAtomicUserInteraction:

    @classmethod
    def notify_user(cls, text: str, sleep_sec: int = 1):
        print(text)
        logger.info(f"User Notified of: \"{text}\"")
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    @classmethod
    def request_string(cls, prompt: str, default: str = None, cancel_text: str = None):
        if default is not None:
            prompt = prompt.replace(":", " ")
            prompt = prompt + f"(enter for default [{default}]):"

        if cancel_text:
            prompt = prompt.replace(":", " ")
            prompt = prompt + f"({cancel_text} to cancel):"

        inp = input(prompt).strip()

        if len(inp) == 0 and default:
            ret = default
        elif cls._check_cancel(inp, cancel_text):
            ret = None
        else:
            ret = inp

        logger.info(f"User provided <string> value: {ret}")
        return ret

    @classmethod
    def request_int(cls, prompt: str, min: int = None, max: int = None, default: int = None):
        cancel_text = 'x'
        default_prompt_text = f", <enter> for {default}" if default is not None else ""
        cancel_default_prompt = f"({cancel_text} to cancel{default_prompt_text})"

        if min is not None and max is not None:
            prompt = prompt.replace(":", " ")
            prompt = prompt + f"[between {min} and {max} (inclusive)]{cancel_default_prompt}:"
        elif min is not None:
            prompt = prompt.replace(":", " ")
            prompt = prompt + f"[greater than or equal to {min}]{cancel_default_prompt}:"
        elif max is not None:
            prompt = prompt.replace(":", " ")
            prompt = prompt + f"[less than or equal to {max}]{cancel_default_prompt}:"
        else:
            prompt = prompt.replace(":", " ")
            prompt = f"{prompt}{cancel_default_prompt}:"

        while True:
            try:
                ret = input(prompt)

                if ret == "":
                    logger.info(f"Using default <int> value {default}. PROMPT: \"{prompt}\"")
                    return default

                if cls._check_cancel(ret, cancel_text):
                    logger.info(f"User cancelled <int> entry. PROMPT: \"{prompt}\"")
                    return None

                parsed = cls.int_tryParse(ret)
                if parsed is None:
                    raise ValueError(f"Invalid integer value {ret}")

                if min is not None and parsed < min:
                    raise Exception(f"Must be greater than {min}")

                if max is not None and parsed > max:
                    raise Exception(f"Must be less than {max}")

                logger.info(f"User provided <int> value: {parsed}. PROMPT: \"{prompt}\"")
                return parsed

            except Exception as e:
                cls.notify_user(f"Invalid Integer entry: {e}")

    @classmethod
    def request_enum(cls, enum, prompt: str = None, cancel_text: str = 'CANCEL SELECTION'):
        if prompt is None:
            prompt = f"Enter {enum.__name__}:"

        if issubclass(enum, Enum):
            enum_num = cls.request_from_dict({x.value: x.name for x in enum}, prompt, cancel_text)
            if enum_num is None:
                return None
            else:
                return enum(enum_num)
        else:
            raise TypeError(f"Input must be of type Enum but {type(enum)} was provided")

    @classmethod
    def request_float(cls, prompt: str, min: float = None, max: float = None, default: float = None):
        cancel_text = 'x'
        default_prompt_text = f", <enter> for {default}" if default is not None else ""
        cancel_default_prompt = f"({cancel_text} to cancel{default_prompt_text})"

        if min is not None and max is not None:
            prompt = prompt.replace(":", " ")
            prompt = prompt + f"[between {min} and {max} (inclusive)]{cancel_default_prompt}:"
        elif min is not None:
            prompt = prompt.replace(":", " ")
            prompt = prompt + f"[greater than or equal to {min}]{cancel_default_prompt}:"
        elif max is not None:
            prompt = prompt.replace(":", " ")
            prompt = prompt + f"[less than or equal to {max}]{cancel_default_prompt}:"
        else:
            prompt = prompt.replace(":", " ")
            prompt = f"{prompt}{cancel_default_prompt}:"

        while True:
            try:
                ret = input(prompt)

                if ret == "":
                    logger.info(f"Using default <float> value: {default}. PROMPT: \"{prompt}\"")
                    return default

                if cls._check_cancel(ret, cancel_text):
                    logger.info(f"User cancelled entry of <float> value. PROMPT: \"{prompt}\"")
                    return None

                inp = float(ret)
                if min and inp < min:
                    raise Exception(f"Must be greater than or equal to {min}")

                if max and inp > max:
                    raise Exception(f"Must be less than or equal to {max}")

                logger.info(f"User provided <float> value: {inp}. PROMPT: \"{prompt}\"")
                return inp
            except Exception as e:
                cls.notify_user(f"invalid float entry: {e}")

    @classmethod
    def request_guid(cls, prompt: str):
        while True:
            inp = input(prompt)
            if (len(inp)) == 24:
                logger.info(f"User provided <guid> value: {inp}. PROMPT: \"{prompt}\"")
                return inp
            else:
                cls.notify_user("Invalid Guid...")

    @classmethod
    def request_date(cls, prompt: str = None, cancel_text='x'):
        if prompt is None:
            prompt = "Date"

        prompt.replace(":", "")

        prompt = prompt + f"({cancel_text} to cancel, <Enter> for current date):"

        while True:
            inp = input(f"{prompt}")
            try:
                if inp == '':
                    date_stamp = datetime.datetime.now().date()
                    print(f"using: {date_stamp}")
                elif cls._check_cancel(inp, cancel_text):
                    logger.info(f"User cancelled entry of <date> value: PROMPT: \"{prompt}\"")
                    return None
                else:
                    date_stamp = tv.date_tryParse(inp)
                    if date_stamp is None:
                        raise
                break
            except:
                print("invalid date format")

        logger.info(f"User provided <date> value: {date_stamp}. PROMPT: \"{prompt}\"")
        return date_stamp

    @classmethod
    def request_datetime(cls, prompt: str = None, cancel_text='x', include_ms: bool = False):
        if prompt is None:
            prompt = "Datetime"

        prompt.replace(":", "")

        prompt = prompt + f"({cancel_text} to cancel, <Enter> for current datetime):"

        while True:
            inp = input(f"{prompt}")
            try:
                if inp == '':
                    date_stamp = datetime.datetime.now()
                    print(f"using: {date_stamp}")
                elif cls._check_cancel(inp, cancel_text):
                    logger.info(f"User cancelled entry of <datetime> value: PROMPT: \"{prompt}\"")
                    return None
                else:
                    date_stamp = parser.parse(inp)
                break
            except:
                print("invalid date format")

        if not include_ms:
            date_stamp = datetime.datetime.combine(date_stamp, datetime.datetime.min.time())

        logger.info(f"User provided <datetime> value: {date_stamp}. PROMPT: \"{prompt}\"")
        return date_stamp

    @classmethod
    def request_list(cls, request_prompt: str) -> List[str]:
        ret = []
        while True:
            item = cls.request_string(request_prompt)
            if item is None:
                break
            ret.append(item)

        if len(ret) == 0:
            return None

        return ret

    @classmethod
    def request_use_list(cls, use_prompt: str, request_prompt: str) -> List[str]:
        use = cls.request_bool(use_prompt)

        if not use:
            return None

        return cls.request_list(
            request_prompt=request_prompt)

    @classmethod
    def request_from_list(cls, selectionList: List[T], prompt=None, cancel_text: str = 'CANCEL SELECTION') -> T:
        ret = cls.request_from_dict({ii: item for ii, item in enumerate(selectionList)}, prompt, cancel_text)
        if ret is None:
            return ret

        return selectionList[ret]

    def request_from_objects(cls, selectionList: List[T], objectIdentifier: str, prompt=None,
                             cancel_text: str = 'CANCEL SELECTION') -> T:
        item_id = cls.request_from_list([str(vars(obj)[objectIdentifier]) for obj in selectionList], prompt=prompt,
                                        cancel_text=cancel_text)
        if item_id is None:
            return item_id

        return next(item for item in selectionList if str(vars(item)[objectIdentifier]) == item_id)

    @classmethod
    def request_from_dict(cls, selectionDict: Dict[int, str], prompt=None,
                          cancel_text: str = 'CANCEL SELECTION') -> int:
        if prompt is None:
            prompt = "Choose an Item:"

        cancel = 'X'

        while True:
            print(prompt)
            for key in selectionDict:
                print(f"{key} -- {selectionDict[key]}")

            if cancel_text is not None:
                print(f"{cancel} -- {cancel_text}")

            inp = input("").upper()
            if cls._check_cancel(inp, cancel):
                logger.info(f"User cancelled selection from dict: PROMPT: {prompt}")
                return None

            inp = cls.int_tryParse(inp)

            if (inp or type(inp) == int) and selectionDict.get(inp, None) is not None:
                logger.info(
                    f"User selected value: \"{inp}\" ({selectionDict[inp]}) from dictionary . PROMPT: \"{prompt}\"")
                return inp
            else:
                print("Invalid Entry...")

    @classmethod
    def request_index_from_df(cls,
                              df: pd.DataFrame,
                              prompt: str = None,
                              cancel_text: str = 'CANCEL SELECTION',
                              hide_columns: List[str] = None,
                              return_columns: List[str] = None,
                              additional_options: List[str] = None,
                              **kwargs):
        if prompt is None:
            prompt = "Select an index from the dataframe:"

        cancel = 'X'

        while True:
            print_out = df
            if hide_columns:
                print_out = print_out[[x for x in print_out.columns if x not in hide_columns]]

            ph.pretty_print_dataframe(print_out,
                                      prompt,
                                      prevent_newline_bool=True if additional_options else False,
                                       **kwargs)
            largest_idx = print_out.index.max()
            if additional_options:
                idx = largest_idx + 1
                for x in additional_options:
                    print(f"{idx} -- {x}")
                    idx += 1
                print("\n")

            if cancel_text is not None:
                print(f"{cancel} -- {cancel_text}")

            inp = input("").upper()

            if cls._check_cancel(inp, cancel):
                logger.info(f"User cancelled selection from dataframe . PROMPT: {prompt}")
                return None

            ind = cls.int_tryParse(inp)
            if (ind in df.index) and return_columns is None:
                logger.info(f"User selected value: \"{ind}\" from dataframe . PROMPT: {prompt}")
                return ind
            elif (ind in df.index) and len(return_columns) > 0:
                logger.info(f"User selected value: \"{ind}\" from dataframe . PROMPT: {prompt}")
                return (df.at[ind, x] for x in return_columns if x in df.columns)
            elif additional_options and ind in range(largest_idx + 1, largest_idx + len(additional_options) + 1):
                return additional_options[ind - largest_idx - 1]
            else:
                print("Invalid Entry...")

    @classmethod
    def request_open_filepath(cls,
                              prompt: str = None,
                              title: str = None,
                              filetypes: Tuple[Tuple[str, str], ...] = None,
                              **open_file_kwargs):
        root = tkinter.Tk()

        if prompt is not None:
            cls.notify_user(text=prompt)

        if filetypes is None:
            filetypes = ()

        if filetypes is None:
            filetypes = (("All Files", "*.*"),)

        if title is None:
            title = "Open File"
        in_path = fd.askopenfilename(title=title, filetypes=filetypes, **open_file_kwargs)
        root.destroy()

        if in_path == '':
            in_path = None

        logger.info(f"User requested opening filepath \"{in_path}\". PROMPT: {prompt}")
        return in_path

    @classmethod
    def pd_column_replacement(cls, df, required_columns) -> Dict:
        missing_columns = [column for column in required_columns if column not in df.columns]
        additional_columns = [column for column in df.columns if column not in required_columns]

        if len(missing_columns) == 0 or len(additional_columns) == 0:
            return {}

        resp = cls.request_yes_no(
            prompt=f"The following columns are missing from dataset:  [{[col for col in missing_columns]}]. "
                   f"\nWould you like to substitute from additional columns: [{[col for col in additional_columns]}]",
            cancel_text=None)

        if resp is False:
            return {}

        remaining_to_evaluate = missing_columns
        replacements = {}
        while len(remaining_to_evaluate) > 0:
            options = [x for x in additional_columns if x not in replacements.keys()]
            replacement = cls.request_from_list(options, f"Any replacement for column [{remaining_to_evaluate[0]}]")
            if replacement is not None:
                replacements[replacement] = remaining_to_evaluate[0]
            remaining_to_evaluate.pop(0)

        logger.info(f"User defined replacement columns for dataframe: {replacements}")
        return replacements

    # TODO: Allow to select a filepath with specified columns without actually retuning the data
    # def request_csv_filepath_with_specified_columns(self,
    #                                                 columns: List,
    #                                                 title:
    #                                                 ):

    @classmethod
    def request_data_from_csv_with_specified_columns(cls,
                                                     column_type_definition: Dict,
                                                     title: str = None,
                                                     case_sensitive_headers: bool = False,
                                                     allow_partial: bool = False,
                                                     fill_missing: bool = False,
                                                     filepath: str = None,
                                                     keep_extra: bool = False,
                                                     required_columns: List = None) -> FileContentReturn:

        # Direct user of what is required
        required_columns = required_columns if required_columns else [key for key, value in
                                                                      column_type_definition.items()]

        error = None
        while True:
            if filepath is None:
                if allow_partial:
                    text = "AT LEAST A SUBSET OF"
                else:
                    text = "ALL OF"
                cls.notify_user(
                    f"Please select a .csv file containing {text} the columns:\n\t" + "\n\t".join(required_columns),
                    sleep_sec=0)

                # Request Filepath from user
                filepath = cls.request_open_filepath(title=title, filetypes=(("CSV Files", "*.csv"),))

            # Get file contents
            if filepath is None or filepath == '':
                logger.info(f"User cancelled reading in .csv. PROMPT: {title}")
                error = f"user cancelled"
                ret = None
                break

            # Attempt to read a csv in various encodings
            df = None
            encodings = ['cp1252', 'utf-8', 'ISO-8859-1']
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except:
                    continue

            # Return
            if df is None:
                error = f"unable to read csv. No valid encoding (must be in {[x for x in encodings]})"
                ret = None
                break

            cls.notify_user(
                f"The selected file [{filepath}] \nhas the following columns:\n\t" + "\n\t".join(df.columns),
                sleep_sec=0)

            try:
                ret = clean_a_dataframe(df,
                                        column_type_definition=column_type_definition,
                                        allow_partial_columnset=allow_partial,
                                        case_sensitive=case_sensitive_headers,
                                        fill_missing=fill_missing,
                                        column_name_replacement=cls.pd_column_replacement(df,
                                                                                          required_columns),
                                        keep_extra=keep_extra)
                break
            except Exception as e:
                e_txt = f"Error when reading the csv file: {str(e)}"
                cls.notify_user(text=e_txt)
                error = e_txt
                ret = None
                break

        return FileContentReturn(
            file_path=filepath,
            data=ret,
            error=error
        )

    @classmethod
    def request_save_filepath(cls, prompt: str = None, filetypes: Tuple[Tuple[str, str]] = None, **save_file_kwargs):
        root = tkinter.Tk()

        if prompt is not None:
            cls.notify_user(text=prompt)

        if filetypes is None:
            filetypes = (("All Files", "*.*"),)
        in_path = fd.asksaveasfilename(filetypes=filetypes, **save_file_kwargs)
        root.destroy()

        if in_path == '':
            in_path = None

        # Append the correct filetype .* if not included
        if in_path is not None and in_path.find('.') == -1 and filetypes is not None and filetypes[0][1] != "*.*":
            in_path += filetypes[0][1]

        logger.info(f"User selected a filepath for saving \"{in_path}\". PROMPT: {prompt}")
        return in_path

    @classmethod
    def request_directory(cls, prompt: str = None, **directory_kwargs):
        root = tkinter.Tk()

        if prompt is not None:
            cls.notify_user(text=prompt)

        ret_dir = fd.askdirectory(**directory_kwargs)
        root.destroy()

        if ret_dir == '':
            ret_dir = None

        logger.info(f"User selected a directory \"{ret_dir}\". PROMPT: {prompt}")
        return ret_dir

    @classmethod
    def request_you_sure(cls, prompt=None, cancel_text: str = 'CANCEL SELECTION'):
        if prompt is None:
            prompt = "Are you sure?"

        return cls.request_from_dict({1: "Yes", 2: "No"}, prompt, cancel_text=cancel_text)

    @classmethod
    def request_bool(cls, prompt=None, cancel_text: str = 'CANCEL SELECTION'):
        inp = cls.request_from_dict({1: "True", 2: "False"}, prompt, cancel_text=cancel_text)
        if inp == 1:
            ret = True
        elif inp == 2:
            ret = False
        elif inp is None:
            ret = None
        else:
            raise NotImplementedError(f"Unhandled return [{inp}] from request_from_dict")

        logger.info(f"User selected <bool> {ret}. PROMPT: {prompt}")
        return ret

    @classmethod
    def request_yes_no(cls, prompt: str = None, cancel_text: Optional[str] = 'CANCEL SELECTION') -> bool:
        inp = cls.request_from_dict({1: "Yes", 2: "No"}, prompt, cancel_text=cancel_text)

        if inp == 1:
            ret = True
        elif inp == 2:
            ret = False
        elif inp is None:
            ret = None
        else:
            raise NotImplementedError(f"Unhandled return [{inp}] from request_from_dict")

        logger.info(f"User selected <bool> {ret}. PROMPT: {prompt}")
        return ret

    @classmethod
    def float_as_currency(cls, val: float):
        return "${:,.2f}".format(round(val, 2))

    @classmethod
    def int_tryParse(cls, value):
        try:
            return int(value)
        except:
            logger.info(f"Unable to parse the value {value} to type <int>")
            return None

    @classmethod
    def pprint_items(cls, items, header: str = None):
        if header:
            print(header)
        pprint(items)

    @classmethod
    def pretty_print_dataframe(cls,
                               **kwargs
                               ):
        print(
            DeprecationWarning(f"This has been deprecated in favor of cooptools.pandashelpers.pretty_print_dataframe"))
        ph.pretty_print_dataframe(**kwargs)

    @classmethod
    def try_save_dataframe(cls, df: pd.DataFrame, filepath: str):
        while True:
            try:
                df.to_csv(filepath, index=False)
                break
            except Exception as e:
                cls.notify_user(f"Unable to save file: {e}")
                cont = cls.request_yes_no(prompt=f"Retry?")
                if cont == 0: return False

        cls.notify_user(f"File saved at: {filepath}")
        return True

    @classmethod
    def _check_cancel(cls, value: str, cancel_text: str = None):
        if value in ('', None):
            return True

        if cancel_text is not None and cancel_text.upper() == value.upper():
            return True

        return False

    @classmethod
    def request_float_tuple(cls,
                            prompt: StringProvider = None,
                            min: int = None,
                            max: int = None,
                            cancel_text: str = None,
                            len_limit: int = None):
        cancel_text = cancel_text if cancel_text is not None else 'x'
        default_prompt_text = f", in the format: 'x.0, y.0, z.0, ...'"

        cancel_default_prompt = f"({cancel_text} to cancel{default_prompt_text})"

        prompt = resolve_prompt_text(prompt, default=f"Enter a Tuple:")

        if min is not None and max is not None:
            prompt = prompt + f" [between {min} and {max} (inclusive)] {cancel_default_prompt}:"
        elif min is not None:
            prompt = prompt + f" [greater than or equal to {min}] {cancel_default_prompt}:"
        elif max is not None:
            prompt = prompt + f" [less than or equal to {max}] {cancel_default_prompt}:"
        else:
            prompt = f"{prompt} {cancel_default_prompt}:"

        while True:
            try:
                ret = input(prompt)

                if cls._check_cancel(ret, cancel_text):
                    logger.info(f"User cancelled entry of <float> value. PROMPT: \"{prompt}\"")
                    return None

                splitted = ret.split(',')

                converted = tuple(float(x) for x in splitted)

                if len_limit is not None and len(converted) > len_limit:
                    raise ValueError(
                        f"Too many values provided. No more than {len_limit} expected but {len(converted)} entered")

                for x in converted:
                    if min is not None and x < min:
                        raise Exception(f"All values must be greater than or equal to {min}")

                    if max is not None and x > max:
                        raise Exception(f"All values must be less than or equal to {max}")

                logger.info(f"User provided <float> value: {ret}. PROMPT: \"{prompt}\"")
                return converted
            except Exception as e:
                cls.notify_user(f"invalid float entry: {e}")

    @classmethod
    def request_float_points(
            cls,
            prompt: StringProvider = None,
            gt: int = None,
            gte: int = None,
            lt: int = None,
            lte: int = None,
            eq: int = None,
            min: float = None,
            max: float = None,
            len_limit: int = None
    ) -> List[vec.FloatVec]:
        prompt = resolve_prompt_text(prompt, default="Enter some points")

        sub_entries = []
        if gt is not None:
            sub_entries.append(f"more than {gt}")
        if gte is not None:
            sub_entries.append(f"at least {gte}")
        if lt is not None:
            sub_entries.append(f"less than {lt}")
        if lte is not None:
            sub_entries.append(f"no more than {lte}")
        if eq is not None:
            sub_entries.append(f"exactly {eq}")

        sub = ''
        if len(sub_entries) > 0:
            sub = ' (' + ','.join(sub_entries) + ')'

        prompt = f"{prompt}{sub}"

        print(prompt)

        points = []
        ii = 0
        while True:
            new = cls.request_float_tuple(
                prompt=f"Get point {ii}",
                min=min,
                max=max,
                len_limit=len_limit
            )

            if new is None and gte and len(points) < gte:
                print(f"User cancelled")
                return None

            if new is None and gt and len(points) < gt + 1:
                print(f"User cancelled")
                return None

            if new is None and len(points) == 0:
                print(f"User cancelled")
                return None

            if new is None:
                return points

            points.append(new)

            if eq is not None and len(points) == eq:
                return points

            if lte is not None and len(points) == lte:
                return points

            if lt is not None and len(points) == lt - 1:
                return points

            ii += 1


if __name__ == "__main__":
    get_floats = CliAtomicUserInteraction.request_float_points(prompt=lambda: f'Get a some float tuples',
                                                               min=0,
                                                               max=100,
                                                               len_limit=2)
    print(get_floats)