# Cartwheels  Copyright (C) 2024  Alwyn Aswin

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True, eq=True)
class PkgNfo:
    """
    Contains detailed information about the package
    """
    name: str = field(default_factory=str)
    version: str = field(default_factory=str)
    dependencies: Tuple['PkgNfo'] = field(default_factory=Tuple)

    def get_key(self):
        return PkgNfo.static_get_key(self.name, self.version)

    @staticmethod
    def static_get_key(name: str, ver: str):
        return f"{name}::{ver}"
