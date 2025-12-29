from .br_utils import BrUtils
from .cnpj import (
    CnpjUtils,
    cnpj_utils,
)
from .cpf import (
    CpfUtils,
    cpf_utils,
)

__all__ = [
    "BrUtils",
    "CnpjUtils",
    "CpfUtils",
    "br_utils",
    "cnpj_utils",
    "cpf_utils",
]

__version__ = "1.0.0"

br_utils = BrUtils()
