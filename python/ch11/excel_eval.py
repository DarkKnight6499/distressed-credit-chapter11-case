"""Evaluate the model's small Excel formula subset without external dependencies."""

import ast
import json
import operator
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl.utils.cell import range_boundaries

# Configuration
REFERENCE_PATTERN = re.compile(r"(?:(?:'[^']+'|[A-Za-z_][A-Za-z0-9_]*)!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?")
TOKEN_PATTERN = re.compile(r'\s*("(?:[^"]|"")*"|(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?|<>|<=|>=|[+*/(),&=<>-]|[A-Za-z_][A-Za-z0-9_]*)')
XML_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
COMPARISON = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge, ast.Eq: operator.eq, ast.NotEq: operator.ne}


class FormulaEvaluator:
    """Only allow cell references, arithmetic, comparisons and listed functions."""

    def __init__(self, workbook):
        self.workbook = workbook
        self.cache = {}
        self.visiting = set()

    def cell(self, sheet, coordinate):
        key = (sheet, coordinate.replace("$", ""))
        if key in self.cache:
            return self.cache[key]
        if key in self.visiting:
            raise ValueError(f"Circular reference: {key}")
        self.visiting.add(key)
        value = self.workbook[sheet][key[1]].value
        if isinstance(value, str) and value.startswith("="):
            value = self.formula(sheet, value)
        self.visiting.remove(key)
        self.cache[key] = value
        return value

    def _range(self, sheet, address):
        bounds = range_boundaries(address.replace("$", ""))
        values = []
        for row in self.workbook[sheet].iter_rows(min_col=bounds[0], min_row=bounds[1], max_col=bounds[2], max_row=bounds[3]):
            values.extend(self.cell(sheet, cell.coordinate) for cell in row)
        return values

    def _translate(self, sheet, formula):
        expression = []
        position = 1
        while position < len(formula):
            if formula[position].isspace():
                position += 1
                continue
            reference = REFERENCE_PATTERN.match(formula, position)
            if reference:
                text = reference.group()
                target, address = text.rsplit("!", 1) if "!" in text else (sheet, text)
                target = target.strip("'")
                function = "RANGE" if ":" in address else "CELL"
                expression.append(f"{function}({json.dumps(target)},{json.dumps(address)})")
                position = reference.end()
                continue
            token = TOKEN_PATTERN.match(formula, position)
            if not token:
                raise ValueError(f"Unsupported formula at {formula[position:]}")
            text = token.group(1)
            if text.startswith('"'):
                text = json.dumps(text[1:-1].replace('""', '"'))
            expression.append({"=": "==", "<>": "!="}.get(text, text))
            position = token.end()
        return "".join(expression)

    def formula(self, sheet, formula):
        return self._evaluate(ast.parse(self._translate(sheet, formula), mode="eval").body)

    @staticmethod
    def _flatten(values):
        return [item for value in values for item in (value if isinstance(value, list) else [value])]

    def _evaluate(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return self._evaluate(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        if isinstance(node, ast.BinOp):
            left, right = self._evaluate(node.left), self._evaluate(node.right)
            if isinstance(node.op, ast.BitAnd):
                return str(left) + str(right)
            if type(node.op) not in BINARY:
                raise ValueError("Unsupported operator")
            return BINARY[type(node.op)](left, right)
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            return COMPARISON[type(node.ops[0])](self._evaluate(node.left), self._evaluate(node.comparators[0]))
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            raise ValueError("Unsupported formula syntax")
        name = node.func.id
        if name == "IF":
            return self._evaluate(node.args[1] if self._evaluate(node.args[0]) else node.args[2])
        args = [self._evaluate(argument) for argument in node.args]
        if name == "CELL":
            return self.cell(*args)
        if name == "RANGE":
            return self._range(*args)
        if name == "SUM":
            return sum(value for value in self._flatten(args) if isinstance(value, (int, float)))
        if name in ("MIN", "MAX"):
            return (min if name == "MIN" else max)(self._flatten(args))
        if name == "ABS":
            return abs(args[0])
        if name == "AND":
            return all(args)
        if name == "SUMIF":
            criteria_range, criterion, sum_range = args
            if len(criteria_range) != len(sum_range):
                raise ValueError("SUMIF dimensions differ")
            if isinstance(criterion, (int, float)):
                match = lambda value: value == criterion
            else:
                parsed = re.fullmatch(r"(<=|>=|<>|<|>|=)?(-?\d+(?:\.\d*)?)", criterion)
                if not parsed:
                    raise ValueError("Unsupported SUMIF criterion")
                compare = {"<": operator.lt, ">": operator.gt, "<=": operator.le, ">=": operator.ge, "<>": operator.ne, "=": operator.eq}[parsed.group(1) or "="]
                target = float(parsed.group(2))
                match = lambda value: compare(value, target)
            return sum(amount for value, amount in zip(criteria_range, sum_range) if match(value))
        raise ValueError(f"Unsupported function: {name}")

    def all_formulas(self):
        return {(sheet.title, cell.coordinate): self.cell(sheet.title, cell.coordinate)
                for sheet in self.workbook for row in sheet for cell in row if cell.data_type == "f"}


def cache_values(path, workbook):
    """Write evaluated caches while preserving all live formula text."""
    path = Path(path)
    results = FormulaEvaluator(workbook).all_formulas()
    with ZipFile(path) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    for number, sheet in enumerate(workbook, 1):
        member = f"xl/worksheets/sheet{number}.xml"
        document = ET.fromstring(files[member])
        for cell in document.findall(f".//{{{XML_NAMESPACE}}}c"):
            key = (sheet.title, cell.attrib["r"])
            if key not in results:
                continue
            value = results[key]
            cached = cell.find(f"{{{XML_NAMESPACE}}}v")
            if cached is None:
                cached = ET.SubElement(cell, f"{{{XML_NAMESPACE}}}v")
            if isinstance(value, str):
                cell.set("t", "str")
                cached.text = value
            else:
                cell.attrib.pop("t", None)
                cached.text = str(value)
        files[member] = ET.tostring(document, encoding="utf-8", xml_declaration=True)
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return results
