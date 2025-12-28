'''
    Constants, secrets and logging configuration system
'''
import os
from logging.config import dictConfig
from typing import Any

import toml
import yaml


class ConfigNotFound(Exception):  # noqa N818
    pass


class ConfigError(Exception):
    pass


class EnvConfig:  # noqa R0903
    '''
        Get environ variable
    '''

    def __getattr__(self, key: str) -> Any:
        if key.isupper():
            try:
                return os.environ[key]
            except KeyError as exc:
                raise ConfigNotFound(key) from exc

        return super().__getattribute__(key)


class SecretConfig:  # noqa R0903
    '''
        Pop environ variable
    '''

    def __getattr__(self, key: str) -> Any:
        if key.isupper():
            try:
                return os.environ.pop(key)
            except KeyError as exc:
                raise ConfigNotFound(key) from exc

        return super().__getattribute__(key)


class Config:  # noqa R0903
    """
        export CONFIG='/path/to/base_config.yaml;/path/to/config.toml'

        .. code-block:: python
            from config import Config

            CFG = Config()

            CFG.PUBLIC_URL - get from config files
            CFG.ENV.CONFIG - get from os env
            CFG.SECRET.KEY - get from os env and clean
    """

    data: dict = {}
    env_config: EnvConfig = EnvConfig()
    secret: SecretConfig = SecretConfig()

    def __init__(self) -> None:
        if 'CONFIG' not in os.environ:
            raise ConfigError('Environ var CONFIG not found')

        _data = {}

        for cfg in os.environ['CONFIG'].split(';'):
            if cfg.endswith('.yaml') or cfg.endswith('.yml'):
                _data.update(yaml.safe_load(open(cfg, encoding='utf8')))
            if cfg.endswith('.toml'):
                _data.update(toml.load(open(cfg, encoding='utf8')))

        self.data = {key.upper(): val for key, val in _data.items()}

    def __getattr__(self, key: str) -> Any:
        if key == 'ENV':
            return self.env_config

        if key == 'SECRET':
            return self.secret

        if key.isupper():
            try:
                return self.data[key]
            except KeyError as exc:
                raise ConfigNotFound(key) from exc

        return super().__getattribute__(key)


class LoggingConfig:
    """
        export CONFIG='/path/to/base_log_config.yaml;/path/to/logging.toml'

        .. code-block:: python
            from config import LoggingConfig

            CFG = LoggingConfig({
                'loggers': {
                    'aiohttp.access': {  # local overriding
                        'level': 'ERROR',
                    }
                }
            })
    """

    data: dict = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {},
        'filters': {},
        'handlers': {},
        'loggers': {},
        'root': {},
    }

    def __init__(self, extra_config: dict | None = None, apply_config: bool = True) -> None:
        if 'LOGGING' not in os.environ:
            raise ConfigError('Environ var LOGGING not found')

        for cfg in os.environ['LOGGING'].split(';'):
            if cfg.endswith('.yaml') or cfg.endswith('.yml'):
                self.append_config(yaml.safe_load(open(cfg, encoding='utf8')))
            if cfg.endswith('.toml'):
                self.append_config(toml.load(open(cfg, encoding='utf8')))

        if extra_config:
            self.append_config(extra_config)

        if apply_config:
            self.apply_config()

    def append_config(self, data: dict) -> None:
        ''' Update configuration '''
        for section in self.data:
            if section in data:
                if section in {'version', 'disable_existing_loggers'}:
                    self.data[section] = data[section]
                else:
                    self.data[section].update(data[section])

    def apply_config(self) -> None:
        ''' Apply configuration '''
        dictConfig(self.data)
