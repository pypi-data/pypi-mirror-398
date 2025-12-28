"""Configuration for the pytest test suite."""

from os import environ

from profiler_cub import METADATA

environ[f"{METADATA.env_variable}"] = "test"
