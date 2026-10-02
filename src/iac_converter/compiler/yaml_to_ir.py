# src/iac_converter/compiler/yaml_to_ir.py

from iac_converter.ir import ProjectIR
from iac_converter.parser.yaml_parser import parse_yaml


def compile_yaml(source: str) -> ProjectIR:
    return parse_yaml(source)