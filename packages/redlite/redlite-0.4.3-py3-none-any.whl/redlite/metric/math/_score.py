from redlite import NamedMetric
from ._parser import parse, Node, Number, Tuple, Binary, Matrix, Function1, Function2, Negation, PlusMinus
import re
import math
from typing import cast


def score(expected: str, actual: str) -> float:
    if expected == actual:
        return 1.0
    expected = norma(expected)
    actual = norma(actual)
    if expected == actual:
        return 1.0
    parsed_expected = parse(expected)
    parsed_actual = parse(actual)
    if parsed_actual is None or parsed_expected is None:
        return 0.0
    if parsed_expected == parsed_actual:
        return 1.0
    parsed_expected = simplify(parsed_expected)
    parsed_actual = simplify(parsed_actual)
    if parsed_actual == parsed_expected:
        return 1.0
    return 0.0


def boxed(string: str) -> str | None:
    # extracts match expression from with \\boxed{...} construct. Trick is to follow nested curly brackets, e.g.
    # "\\boxed{\\frac{1}{3}}" => "\\frac{1}{3}"
    string = string.replace("\n", " ")
    pieces = list(m.start() for m in re.finditer(r"\\boxed{", string))
    if len(pieces) == 0:
        return None
    start = pieces[-1]
    string = string[start:].strip()  # strip everything before the last \\boxed
    for i in range(10):
        modified = re.sub(r"\{([^{}]+)+\}", f"<group-{i}>\\1</group-{i}>", string)
        if modified == string:
            break
        string = modified

    mtc = re.search(r"\\boxed<group-(\d+)>", string)
    if mtc is None:
        return None
    level = mtc.group(1)
    mtc = re.search(rf"\\boxed<group-{level}>(.+?)</group-{level}>", string)
    if mtc is None:
        return None
    content = mtc.group(1)
    content = re.sub(r"<group-\d+>", "{", content)
    content = re.sub(r"</group-\d+>", "}", content)

    return content


def norma(s: str) -> str:
    s = re.sub(r"\^\\circ\s*$", "", s)  # 5^\circ =>5
    s = re.sub(r"°\s*$", "", s)  # 55° => 55
    s = re.sub(r"\\(mbox|text)\{\s*inches\}\^2$", "", s)
    s = re.sub(r"\\(mbox|text)\{\s*cents\}$", "", s)
    s = re.sub(r"\\(mbox|text)\{\s*cm\}\^2$", "", s)
    s = re.sub(r"\\%$", "", s)  # 25% => 25
    s = re.sub(r"^x\s+\\in\s+", "", s)  # x\in (1, 5] => (1, 5]
    s = re.sub(r"^x\s*=", "", s)  # x = 5 => 5
    s = re.sub(r",\\!\s*", "", s)  # 10,\! 000 => 10000
    s = re.sub(r"(\d),(0\d+)", r"\1\2", s)  # 10,000 => 10000
    s = re.sub(r"^\\\$", "", s)  # $32 => 32
    s = re.sub(r"(\d)_\d", r"\1", s)  # ignore integer base: 1010_2 => 1010
    s = re.sub(r"(\d)_\{\d+\}", r"\1", s)  # ignore integer base: 1010_{16} => 1010
    s = re.sub(r"^([A-Z][a-z]+)$", r"\\text{\1}", s)  # wrap naked text into \\text{}
    s = re.sub(r"\\,", " ", s)  # remove LaTeX thin spaces
    return s


def boxed_score(expected, actual):
    actual = boxed(actual)
    if actual is None:
        return 0.0
    return score(expected, actual)


class BoxedMathMetric(NamedMetric):
    """
    Metric to judge 'boxed' math expressions. For example: "\\boxed{1/3}" vs "\\boxed{\\frac{1}{3}}"
    """

    def __init__(self):
        super().__init__("math-metric", boxed_score)


class MathMetric(NamedMetric):
    """
    Metric to judge 'naked' math expressions. For example: "1/3" vs "\\frac{1}{3}"
    """

    def __init__(self):
        super().__init__("math-metric", boxed_score)


def simplify(node: Node) -> Node:
    if node.type == "plus-minus":
        # top-level PlusMinus => convert to tuple
        node = cast(PlusMinus, node)
        return Tuple(
            values=(
                Binary(name="+", op1=node.values[0], op2=node.values[1]),
                Binary(name="-", op1=node.values[0], op2=node.values[1]),
            )
        )
    if node.type == "function1":
        node = cast(Function1, node)
        node.op1 = simplify(node.op1)
        if node.name == "\\sqrt" and node.op1.type == "number":
            op1 = cast(Number, node.op1)
            return Number(value=math.sqrt(op1.value))
    if node.type == "negation":
        node = cast(Negation, node)
        node.op = simplify(node.op)
        if node.op.type == "number":
            op = cast(Number, node.op)
            return Number(value=-op.value)
    if node.type == "function2":
        node = cast(Function2, node)
        if node.name == "frac":
            node.op1 = simplify(node.op1)
            node.op2 = simplify(node.op2)
            if node.op1.type == "number" and node.op2.type == "number":
                op1 = cast(Number, node.op1)
                op2 = cast(Number, node.op2)
                # replace with computed Number
                return Number(value=op1.value / op2.value)
        elif node.name == "\\sqrt":
            node.op1 = simplify(node.op1)
            node.op2 = simplify(node.op2)
            if node.op2.type == "number" and node.op1.type == "number":
                op1 = cast(Number, node.op1)
                op2 = cast(Number, node.op2)
                return Number(value=op1.value ** (1 / op2.value))
    if node.type == "binary":
        node = cast(Binary, node)
        if node.name == "/":
            node.op1 = simplify(node.op1)
            node.op2 = simplify(node.op2)
            if node.op1.type == "number" and node.op2.type == "number":
                # replace with computed Number
                op1 = cast(Number, node.op1)
                op2 = cast(Number, node.op2)
                return Number(value=op1.value / op2.value)
    if node.type == "matrix":
        node = cast(Matrix, node)
        simplified_rows = []
        for row in node.rows:
            simplified_rows.append(tuple(simplify(n) for n in row))
        node.rows = tuple(simplified_rows)
    if node.type in ("tuple", "triple", "quad", "interval"):
        node = cast(Tuple, node)
        node.values = tuple(simplify(n) for n in node.values)
    return node
