from configparser import ConfigParser
import logging
from cooptools import os_manip as osm
import os
from typing import Iterable, Callable, Dict, List, Optional, Union
import json
from dataclasses import dataclass
from cooptools.typevalidation import bool_tryparse
from cooptools import typeProviders as tp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CONFIG_NOT_SET_TXT = f"Config file path has not been set"


class ConfigStateException(Exception):
    def __init__(self, txt: str = None):
        logger.error(txt)
        super().__init__(txt)


def missing_headers_in_json_file(config_filepath: str, headers: str):
    file_config = osm.load_json_data_to_dict(config_filepath)

    missing = []
    for header in headers:
        if header not in file_config.keys():
            missing.append(header)

    return missing


def resolve_from_json_file(config_filepath: str,
                           config: str,
                           is_bool: bool = False,
                           fallback_val_provider=None,
                           fallback_None: bool = False,
                           falback_val=None
                           ):
    file_config = osm.load_json_data_to_dict(config_filepath)

    if config not in file_config.keys() and fallback_None is True:
        return None

    if falback_val is not None:
        fallback_val_provider = falback_val

    if config not in file_config.keys() and fallback_val_provider is not None:
        return tp.resolve(fallback_val_provider)

    if config not in file_config.keys():
        raise ValueError(f"The value {config} was not found in config")

    ret = file_config[config]

    if is_bool:
        ret = bool_tryparse(ret)

    if ret in [None, "null", "None", ""]:
        ret = None

    return ret


def _resolve_bool(val: str):
    if val.upper() in ['F', 'FALSE', 0]:
        return False
    elif val.upper() in ['T', 'TRUE', 1]:
        return True

    raise ValueError(f"The config val: {val} is unrecognized as bool config")


linesProvider = Union[List[str], Callable[[Optional[Dict]], List[str]]]


@dataclass(frozen=True)
class FileCreationArgs:
    fileType: osm.FileType
    linesProvider: linesProvider = None
    linesProviderArgs: Dict = None

    def resolve_lines(self):
        if callable(self.linesProvider):
            return self.linesProvider(self.linesProviderArgs)
        return self.linesProvider

class FileNotSelectedException(Exception):
    def __init__(self):
        err = CONFIG_NOT_SET_TXT
        logger.error(err)
        super().__init__(err)

class FileSelector:
    def __init__(self,
                 file_path_provider: osm.filePathProvider = None,
                 file_creation_args: FileCreationArgs = None):

        self._file_path = None
        if file_path_provider is not None:
            self.set_file(file_path_provider,
                          file_creation_args)

    def resolve_filepath(self,
                         file_path_provider: osm.filePathProvider,
                         file_creation_args: FileCreationArgs = None,
                         invalidate: bool = False):
        if invalidate:
            self._file_path = None

        if self._file_path is not None:
            return self._file_path

        self.set_file(file_path_provider,
                      file_creation_args)

        return self._file_path

    @property
    def FilePath(self):
        return self._file_path

    @property
    def FileDir(self):
        return os.path.dirname(self._file_path)

    @property
    def FileExists(self):
        return osm.check_file_exists(self._file_path)

    def verify_config_set(self):
        if self._file_path is None:
            raise FileNotSelectedException()

    def set_file(self,
                 fp: osm.filePathProvider,
                 file_creation_args: FileCreationArgs = None
                 ):
        # resolve an absolute filepath
        try:
            fp = osm.resolve_absolute_filepath(fp)
        except tp.ResolveFilepathException as e:
            logger.warning(str(e))
            return None

        # create new file if directed
        if not osm.check_file_exists(fp) and file_creation_args:
            osm.create_file(fp,
                            file_type=file_creation_args.fileType,
                            lines=file_creation_args.resolve_lines()
                            )

        # verify path exists
        osm.verify_file_exists(fp)

        # finalize
        logger.info(f"Using file at: {fp}")
        logger.debug(f"File Contents: \n"
                     f"{osm.read_file(file_path=fp)}")
        self._file_path = fp
        return fp


class JsonConfigHandler:
    def __init__(self,
                 file_path_provider: osm.filePathProvider = None,
                 file_creation_args: FileCreationArgs = None):
        self.file_handler = FileSelector(file_path_provider=file_path_provider,
                                         file_creation_args=file_creation_args)

    def verify_headers(self, headers: Iterable[str]):
        self.file_handler.verify_config_set()
        missing_headers = missing_headers_in_json_file(self.file_handler.FilePath, headers=headers)
        return missing_headers is None or len(missing_headers) == 0

    def resolve(self,
                config: str,
                is_bool: bool = False,
                fallback_val_provider=None,
                fallback_None: bool = False,
                fallback_val=None):
        try:
            self.file_handler.verify_config_set()
            val = resolve_from_json_file(self.file_handler.FilePath,
                                         config,
                                         is_bool=is_bool,
                                         fallback_val_provider=fallback_val_provider,
                                         fallback_None=fallback_None,
                                         falback_val=fallback_val)
            logger.debug(f"Value for {config}: {val}")
            return val
        except FileNotSelectedException as e:
            if fallback_val_provider is not None:
                logger.debug(f"Falling back to value for {config}: {fallback_val_provider}")
                return fallback_val_provider
            if fallback_None:
                logger.debug(f"Falling back to value for {config}: {None}")
                return None
            raise e

    @staticmethod
    def build_template(headers: Iterable[str]) -> str:
        temp_dict = {header: "" for header in headers}
        return json.dumps(temp_dict)


class IniConfigHandler:
    def __init__(self,
                 file_path_provider: osm.filePathProvider = None,
                 file_creation_args: FileCreationArgs = None
                 ):
        self.file_handler = FileSelector(file_path_provider=file_path_provider,
                                         file_creation_args=file_creation_args)
        self.parser = ConfigParser()

    def resolve(self, header, name):
        self.file_handler.verify_config_set()
        self._reload_parser()
        val = self.parser.get(header, name)
        logger.debug(f"Value for {header}|{name}: {val}")
        return val

    def _reload_parser(self):
        try:
            self.parser.read(self.file_handler.FilePath)
            logger.debug(f"Config set from directory: {self.file_handler.FilePath}")
        except Exception as e:
            issue = f"Unable to load config from directory: {self.file_handler.FilePath}" \
                    f"\n{e}"
            raise ConfigStateException(issue) from e

    @property
    def Sections(self):
        self.file_handler.verify_config_set()
        self._reload_parser()
        return self.parser.sections()

    @staticmethod
    def build_template(headers: Iterable[str]) -> Iterable[str]:
        lines = []
        for header in headers:
            lines.append(header)
            lines.append("")
        lines.pop(-1)
        return lines


JsonConfigProvider = JsonConfigHandler | Callable[[], JsonConfigHandler]

def resolve_json_config_provider(
        json_config_provider: JsonConfigProvider
):
    return tp.resolve(
        json_config_provider
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    _def = "def"
    con = IniConfigHandler(file_path_provider=r'C:\Users\tburns\AppData\Local\coopazureutils\config2.ini')

    print(con.resolve(_def, "a"), con.resolve(_def, "b"), con.resolve(_def, "c"))

    print(con.Sections)
