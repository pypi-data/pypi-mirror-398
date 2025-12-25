from cooptools.config import IniConfigHandler, ConfigStateException, FileCreationArgs
import unittest
import os
import cooptools.os_manip as osm

HEADER = "def"
CONFIG = 'tests\\testdata\\config.ini'
CONFIG_EMPTY = 'tests\\testdata\\config_empty.ini'
TEMP_CONFIG = 'tests\\testdata\\temp_config.ini'

class Test_Config(unittest.TestCase):

    def test__init_config_state_factory_no_file__dont_create(self):
        # arrange
        if os.path.exists(TEMP_CONFIG):
            os.remove(TEMP_CONFIG)

        # act
        config = IniConfigHandler()

        # assert
        self.assertFalse(os.path.exists(TEMP_CONFIG))

        # clean up
        if os.path.exists(TEMP_CONFIG):
            os.remove(TEMP_CONFIG)

    def test__init_config_state_factory_no_file__create(self):
        # arrange
        if os.path.exists(TEMP_CONFIG):
            os.remove(TEMP_CONFIG)

        # act
        config = IniConfigHandler(file_path_provider=TEMP_CONFIG,
                                  file_creation_args=FileCreationArgs(fileType=osm.FileType.INI,
                                                                      linesProvider=[f"[{HEADER}]"]))

        # assert
        self.assertTrue(os.path.exists(TEMP_CONFIG))
        self.assertTrue(HEADER in config.Sections)

        # clean up
        if os.path.exists(TEMP_CONFIG):
            os.remove(TEMP_CONFIG)

    def test__init_config_state_factory_file__create(self):
        # arrange

        # act
        config = IniConfigHandler(file_path_provider=CONFIG)

        # assert
        self.assertTrue(os.path.exists(CONFIG))
        self.assertTrue(HEADER in config.Sections)
        self.assertTrue(config.resolve(HEADER, 'a'), 1)

    def test__init_config_state_factory_empty_file__create(self):
        # arrange

        # act
        config = IniConfigHandler(file_path_provider=CONFIG_EMPTY)

        # assert
        self.assertTrue(os.path.exists(CONFIG_EMPTY))
        self.assertTrue(HEADER in config.Sections)
        self.assertTrue(config.resolve(HEADER, 'a'), None)