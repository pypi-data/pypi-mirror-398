# DBL Boundary Service
#
# Reference service exposing a governed LLM boundary via DBL and KL.

from .main import create_app, run

__all__ = ["create_app", "run"]

__version__ = "0.2.1"

