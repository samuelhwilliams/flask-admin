from dataclasses import dataclass
from functools import partial
from typing import Protocol, Literal


class Theme(Protocol):
    folder: str  # The templates folder name to use
    base_template: str


class Bootstrap(Protocol):
    swatch: str = 'default'
    fluid: bool = False


@dataclass
class BootstrapTheme(Theme, Bootstrap):
    folder: Literal['bootstrap4']
    base_template: str = 'admin/base.html'

    swatch: str = 'default'
    fluid: bool = False


Bootstrap4Theme = partial(BootstrapTheme, folder='bootstrap4')
