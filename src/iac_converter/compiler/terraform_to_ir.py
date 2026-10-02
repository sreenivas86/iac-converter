# src/iac_converter/compiler/terraform_to_ir.py

from iac_converter.ir import ProjectIR
from iac_converter.parser.terraform_parser import parse_terraform


def compile_terraform(source: str) -> ProjectIR:
    return parse_terraform(source)