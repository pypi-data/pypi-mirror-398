from .cnpj import CnpjFormatterOptions, CnpjGeneratorOptions, CnpjUtils
from .cpf import CpfFormatterOptions, CpfGeneratorOptions, CpfUtils


class BrUtils:
    """Class to consolidate Brazilian utilities for CPF and CNPJ manipulation."""

    __slots__ = ("cnpj", "cpf")

    def __init__(
        self,
        cnpj_formatter: CnpjFormatterOptions | None = None,
        cnpj_generator: CnpjGeneratorOptions | None = None,
        cpf_formatter: CpfFormatterOptions | None = None,
        cpf_generator: CpfGeneratorOptions | None = None,
    ):
        self.cnpj = CnpjUtils(formatter=cnpj_formatter, generator=cnpj_generator)
        self.cpf = CpfUtils(formatter=cpf_formatter, generator=cpf_generator)
