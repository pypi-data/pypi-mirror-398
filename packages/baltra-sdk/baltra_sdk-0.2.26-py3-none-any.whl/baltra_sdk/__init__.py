"""Paquete agregador del Baltra SDK."""

from importlib import import_module as _import_module

__version__ = "0.1.0"


backend = _import_module("baltra_sdk.backend")
lambdas = _import_module("baltra_sdk.lambdas")
shared = _import_module("baltra_sdk.shared")

__all__ = ["backend", "lambdas", "shared", "__version__"]
