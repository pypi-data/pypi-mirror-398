import configparser
import os.path
from typing import Self

from iker.common.utils import logger
from iker.common.utils.strutils import is_blank, trim_to_empty


class Config(object):
    def __init__(self, config_path: str = None):
        self.config_path = trim_to_empty(config_path)
        self.config_parser: configparser.RawConfigParser = configparser.RawConfigParser(strict=False)

    def __len__(self):
        return sum(len(self.config_parser.options(section)) for section in self.config_parser.sections())

    def update(self, tuples: list[tuple[str, str, str]], *, overwrite: bool = False):
        for section, option, value in tuples:
            if not self.config_parser.has_section(section):
                self.config_parser.add_section(section)
            if overwrite or not self.config_parser.has_option(section, option):
                self.config_parser.set(section, option, value)

    def restore(self) -> bool:
        self.config_parser = configparser.RawConfigParser(strict=False)
        if is_blank(self.config_path):
            return False
        try:
            if not os.path.exists(self.config_path):
                raise IOError("file not found")
            self.config_parser.read(self.config_path, encoding="utf-8")
            return True
        except IOError as e:
            logger.exception("Failed to restore config from file <%s>", self.config_path)
        return False

    def persist(self) -> bool:
        if is_blank(self.config_path):
            return False
        try:
            with open(self.config_path, "w") as fh:
                self.config_parser.write(fh)
            return True
        except IOError as e:
            logger.exception("Failed to persist config to file <%s>", self.config_path)
        return False

    def has_section(self, section: str) -> bool:
        return self.config_parser.has_section(section)

    def has(self, section: str, option: str) -> bool:
        return self.config_parser.has_option(section, option)

    def get(self, section: str, option: str, default_value: str = None) -> str:
        if self.config_parser.has_option(section, option):
            return self.config_parser.get(section, option)
        return default_value

    def getint(self, section: str, option: str, default_value: int = None) -> int:
        if self.config_parser.has_option(section, option):
            return self.config_parser.getint(section, option)
        return default_value

    def getfloat(self, section: str, option: str, default_value: float = None) -> float:
        if self.config_parser.has_option(section, option):
            return self.config_parser.getfloat(section, option)
        return default_value

    def getboolean(self, section: str, option: str, default_value: bool = None) -> bool:
        if self.config_parser.has_option(section, option):
            return self.config_parser.getboolean(section, option)
        return default_value

    def set(self, section: str, option: str, value: str):
        if not self.config_parser.has_section(section):
            self.config_parser.add_section(section)
        self.config_parser.set(section, option, value)

    def sections(self) -> list[str]:
        return self.config_parser.sections()

    def options(self, section: str) -> list[str]:
        if not self.config_parser.has_section(section):
            return []
        return self.config_parser.options(section)

    def tuples(self) -> list[tuple[str, str, str]]:
        result = []
        for section in self.config_parser.sections():
            for option in self.config_parser.options(section):
                value = self.config_parser.get(section, option)
                result.append((section, option, value))
        return result


class ConfigVisitor(object):
    def __init__(self, config: Config, section: str, prefix: str = "", separator: str = "."):
        self.config = config
        self.section = section
        self.prefix = prefix
        self.separator = separator

    def __str__(self):
        return self.config.get(self.section, self.prefix)

    def __int__(self):
        return self.config.getint(self.section, self.prefix)

    def __float__(self):
        return self.config.getfloat(self.section, self.prefix)

    def __bool__(self):
        return self.config.getboolean(self.section, self.prefix)

    def __getattr__(self, suffix: str) -> Self:
        return self[suffix]

    def __getitem__(self, suffix: str) -> Self:
        new_prefix = suffix if is_blank(self.prefix) else self.separator.join([self.prefix, suffix])
        return ConfigVisitor(self.config, self.section, new_prefix, self.separator)
