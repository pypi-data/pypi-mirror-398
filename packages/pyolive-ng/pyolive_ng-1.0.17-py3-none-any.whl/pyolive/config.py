import os
import yaml
import logging
from typing import Any

class Config:
    ATHENA_HOME = os.getenv("ATHENA_HOME", os.getcwd())

    def __init__(self, filename: str):
        # 런타임에 환경변수가 있으면 클래스 변수 업데이트
        athena_home_env = os.getenv("ATHENA_HOME")
        if athena_home_env and athena_home_env != Config.ATHENA_HOME:
            Config.ATHENA_HOME = athena_home_env
        
        self.path = os.path.join(Config.ATHENA_HOME, "etc", filename)
        self.config: dict[str, Any] = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {}
        except Exception as e:
            raise RuntimeError(f"Failed to load config file {self.path}") from e

    def get_value(self, key: str, default=None):
        if self.config is None:
            raise RuntimeError("Configuration not loaded.")

        parts = key.split('/')
        val = self.config
        try:
            for part in parts:
                val = val[part]
            return val
        except (KeyError, TypeError):
            return default