from collections.abc import Callable
from dataclasses import fields

from cpf_fmt import CpfFormatter, CpfFormatterOptions
from cpf_gen import CpfGenerator, CpfGeneratorOptions
from cpf_val import CpfValidator


class CpfUtils:
    """Class to manipulate CPF strings."""

    __slots__ = ("formatter", "generator", "validator")

    def __init__(
        self,
        formatter: CpfFormatterOptions | None = None,
        generator: CpfGeneratorOptions | None = None,
    ):
        if formatter is None:
            formatter = CpfFormatterOptions()
        if generator is None:
            generator = CpfGeneratorOptions()

        formatter_kwargs = {
            field.name: getattr(formatter, field.name)
            for field in fields(CpfFormatterOptions)
        }
        generator_kwargs = {
            field.name: getattr(generator, field.name)
            for field in fields(CpfGeneratorOptions)
        }

        self.formatter = CpfFormatter(**formatter_kwargs)
        self.generator = CpfGenerator(**generator_kwargs)
        self.validator = CpfValidator()

    def format(
        self,
        cpf_string: str,
        hidden: bool | None = None,
        hidden_key: str | None = None,
        hidden_start: int | None = None,
        hidden_end: int | None = None,
        dot_key: str | None = None,
        dash_key: str | None = None,
        escape: bool | None = None,
        on_fail: Callable | None = None,
    ) -> str:
        return self.formatter.format(
            cpf_string,
            hidden,
            hidden_key,
            hidden_start,
            hidden_end,
            dot_key,
            dash_key,
            escape,
            on_fail,
        )

    def generate(self, format: bool | None = None, prefix: str | None = None) -> str:
        return self.generator.generate(format, prefix)

    def is_valid(self, cpf_string: str) -> bool:
        return self.validator.is_valid(cpf_string)
