import os

import pytest

from ttutils.config import Config, ConfigError, ConfigNotFound, LoggingConfig


def test_config_ok(monkeypatch):
    monkeypatch.setattr(os, 'environ', {
        'CONFIG': 'tests/cfg.yaml',
        'SECRET': 'SoMeSeCrEt',
        'SOMEVAR': '123',
    })

    CFG = Config()

    assert CFG.KEY == 'val'
    assert CFG.ENV.SOMEVAR == '123'
    assert CFG.SECRET.SECRET == 'SoMeSeCrEt'


def test_config_fail(monkeypatch):
    monkeypatch.setattr(os, 'environ', {'CONFIG': 'tests/cfg.yaml;tests/cfg.toml'})

    CFG = Config()

    with pytest.raises(ConfigNotFound):
        CFG.NOKEY

    with pytest.raises(ConfigNotFound):
        CFG.ENV.SOMEVAR

    with pytest.raises(ConfigNotFound):
        CFG.SECRET.SECRET

    with pytest.raises(AttributeError):
        CFG.SECRET.nokey

    with pytest.raises(AttributeError):
        CFG.ENV.nokey

    with pytest.raises(AttributeError):
        CFG.nokey


def test_config_fail_cfg():
    with pytest.raises(ConfigError):
        Config()


def test_log_ok_yaml(monkeypatch):
    monkeypatch.setattr(os, 'environ', {'LOGGING': 'tests/log.yaml'})

    assert LoggingConfig().data.get('root')
    assert LoggingConfig({'root': {'level': 'INFO'}}).data.get('root')
    assert LoggingConfig(apply_config=False).data.get('root')


def test_log_ok_toml(monkeypatch):
    monkeypatch.setattr(os, 'environ', {'LOGGING': 'tests/log.toml'})

    assert LoggingConfig().data.get('root')
    assert LoggingConfig({'root': {'level': 'INFO'}}).data.get('root')
    assert LoggingConfig(apply_config=False).data.get('root')


def test_log_fail_cfg():
    with pytest.raises(ConfigError):
        LoggingConfig()
