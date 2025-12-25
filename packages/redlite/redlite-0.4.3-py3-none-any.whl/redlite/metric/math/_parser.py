from redlite._core import MissingDependencyError, log

try:
    from pyparsing import (
        ParserElement,
        Word,
        nums,
        alphas,
        Combine,
        Optional,
        Literal,
        Suppress,
        Forward,
        Group,
        one_of,
        infix_notation,
        OpAssoc,
        Or,
        delimited_list,
        ZeroOrMore,
    )
except ImportError as err:
    raise MissingDependencyError("Please install pyparsing") from err

from dataclasses import dataclass
from typing import cast

__all__ = ["parse", "pretty"]


@dataclass(kw_only=True)
class Node:
    type: str


@dataclass(kw_only=True)
class Number(Node):
    type: str = "number"
    value: float

    def __eq__(self, other):
        if not isinstance(other, Number):
            return NotImplemented
        return abs(self.value - other.value) < 1e-5


@dataclass(kw_only=True)
class Variable(Node):
    type: str = "variable"
    name: str


@dataclass(kw_only=True)
class Text(Node):
    type: str = "text"
    text: str


@dataclass(kw_only=True)
class Equation(Node):
    type: str = "equation"
    lh: Node
    rh: Node


@dataclass(kw_only=True)
class Union(Node):
    type: str = "union"
    op1: Node
    op2: Node


@dataclass(kw_only=True)
class Matrix(Node):
    type: str = "matrix"
    rows: tuple[tuple[Node, ...], ...]


@dataclass(kw_only=True)
class Tuple(Node):
    type: str = "tuple"
    values: tuple[Node, ...]

    def __eq__(self, other):
        # lets allow (-1, 2) == (2, -1) because tuple can be unordered
        if not isinstance(other, Tuple):
            return NotImplemented
        return self.values == other.values or self.values == (other.values[1], other.values[0])


@dataclass(kw_only=True)
class Quad(Node):
    type: str = "quad"
    values: tuple[Node, ...]


@dataclass(kw_only=True)
class PlusMinus(Node):
    type: str = "plus-minus"
    values: tuple[Node, ...]


@dataclass(kw_only=True)
class Triple(Node):
    type: str = "triple"
    values: tuple[Node, ...]


@dataclass(kw_only=True)
class Interval(Node):
    type: str = "interval"
    values: tuple[Node, ...]
    brackets: str


@dataclass(kw_only=True)
class Function1(Node):
    type: str = "function1"
    name: str
    op1: Node


@dataclass(kw_only=True)
class Function2(Node):
    type: str = "function2"
    name: str
    op1: Node
    op2: Node


@dataclass(kw_only=True)
class Binary(Node):
    type: str = "binary"
    name: str
    op1: Node
    op2: Node


@dataclass(kw_only=True)
class Negation(Node):
    type: str = "negation"
    op: Node


ParserElement.enable_packrat()

expr = Forward()  # placeholder for recursive expressions

# --- Number ---
number = Combine(Optional(Word(nums)) + "." + Optional(Word(nums))) | Word(nums)
number.set_parse_action(lambda t: Number(value=float(t[0])))

# --- Variables ---
var = Word(alphas, exact=1) | Literal("\\pi") | Literal("\\lambda") | Literal("\\infty")
var.set_parse_action(lambda t: Variable(name=t[0]))

# --- Functions of one and two arguments (TeX-style arg handling) ---
single_digit = Word(nums, exact=1)
single_digit.set_parse_action(lambda t: Number(value=float(t[0])))


def debug(t):
    import pdb

    pdb.set_trace()
    return t


func = Forward()
arg = single_digit | var | Suppress("{") + expr + Suppress("}") | func
frac = Or([Literal("\\frac"), Literal("\\dfrac")]) + arg + arg
frac.set_parse_action(lambda t: Function2(name="frac", op1=t[1], op2=t[2]))
func1 = Or(map(Literal, ["\\sin", "\\cos", "\\cot", "\\arcsin", "\\arccos", "\\sqrt"])) + arg
func1.set_parse_action(lambda t: Function1(name=t[0], op1=t[1]))
sqrt2 = Literal("\\sqrt") + Suppress("[") + single_digit + Suppress("]") + arg
sqrt2.set_parse_action(lambda t: Function2(name="\\sqrt", op1=t[2], op2=t[1]))


def text_parse_action(t):
    text = t[0]
    if text[0] == "(" and text[-1] == ")":
        # \\text{(C)} => \\text{C}
        text = text[1:-1]
    return Text(text=text)


text_func = (
    Suppress(Or([Literal("\\text"), Literal("\\mathbf"), Literal("\\mbox"), Literal("\\textbf")]))
    + Suppress("{")
    + ...
    + Suppress("}")
)

text_func.set_parse_action(text_parse_action)
func <<= frac | sqrt2 | func1 | text_func


# --- lets allow several brace types
lbraces = map(
    Suppress,
    [
        "\\left(",
        "\\left\\{",
        "(",
        "{",
    ],
)
rbraces = map(
    Suppress,
    [
        "\\right)",
        "\\right\\}",
        ")",
        "}",
    ],
)
braced_expr = Or([l + expr + r for (l, r) in zip(lbraces, rbraces)])

atom = func | number | var | braced_expr

negation = Suppress(Literal("-")) + expr
negation.set_parse_action(lambda t: Negation(op=t[0]))

explicit_plus = Suppress(Literal("+")) + expr
explicit_plus.set_parse_action(lambda t: t[0])


def binary_action(t):
    assert len(t) == 1
    t = t[0]
    op2 = t.pop()
    while len(t) > 0:
        assert len(t) % 2 == 0
        name = t.pop()
        op1 = t.pop()
        op2 = Binary(name=name, op1=op1, op2=op2)
    return op2


def implicit_mult_action(t):
    assert len(t) == 1
    t = t[0]
    op2 = t.pop()
    while len(t) > 0:
        op1 = t.pop()
        op2 = Binary(name="*", op1=op1, op2=op2)
    return op2


# --- Operators + - * / ^ _ using infixNotation ---
expr <<= (
    infix_notation(
        atom,
        [
            (one_of("^ _"), 2, OpAssoc.RIGHT, binary_action),
            (
                cast(ParserElement, None),
                2,
                OpAssoc.LEFT,
                implicit_mult_action,
            ),  # implicit multiplication 2x or (1 + x)(3 - y)
            (one_of("* /"), 2, OpAssoc.LEFT, binary_action),
            (one_of("+ -"), 2, OpAssoc.LEFT, binary_action),
        ],
    )
    | negation
    | explicit_plus
)

row = delimited_list(expr, delim="&").set_parse_action(lambda t: tuple(t))
rows = row + ZeroOrMore(Suppress(Literal("\\\\")) + row) + Optional(Suppress(Literal("\\\\")))
rows.set_parse_action(lambda t: tuple(t))

matrix = Group(Suppress(Literal("\\begin{matrix}")) + rows + Suppress(Literal("\\end{matrix}"))) | Group(
    Suppress(Literal("\\begin{pmatrix}")) + rows + Suppress(Literal("\\end{pmatrix}"))
)


def matrix_action(t):
    assert len(t) == 1
    t = t[0]
    assert len(t) == 1
    return Matrix(rows=t[0])


matrix.set_parse_action(matrix_action)


def signed_number_action(t):
    if len(t) == 1:
        return t[0]
    elif len(t) == 2:
        return Number(value=-t[1].value)
    else:
        assert False, t


signed_number = Optional(Literal("-")) + number
signed_number.set_parse_action(signed_number_action)

tuple_ = (
    Suppress("(") + expr + Suppress(",") + expr + Suppress(")")
    | Suppress("\\left(") + expr + Suppress(",") + expr + Suppress("\\right)")
    | Suppress("\\{") + expr + Suppress(",") + expr + Suppress("\\}")
    | expr + Suppress(",") + expr
)
tuple_.set_parse_action(lambda t: Tuple(values=(t[0], t[1])))

triple = (
    Suppress("(") + expr + Suppress(",") + expr + Suppress(",") + expr + Suppress(")")
    | Suppress("\\left(") + expr + Suppress(",") + expr + Suppress(",") + expr + Suppress("\\right)")
    | Suppress("\\{") + expr + Suppress(",") + expr + Suppress(",") + expr + Suppress("\\}")
    | expr + Suppress(",") + expr + Suppress(",") + expr
)
triple.set_parse_action(lambda t: Triple(values=(t[0], t[1], t[2])))

quad = (
    Suppress("(") + expr + Suppress(",") + expr + Suppress(",") + expr + Suppress(",") + expr + Suppress(")")
    | Suppress("\\left(")
    + expr
    + Suppress(",")
    + expr
    + Suppress(",")
    + expr
    + Suppress(",")
    + expr
    + Suppress("\\right)")
    | Suppress("\\{") + expr + Suppress(",") + expr + Suppress(",") + expr + Suppress(",") + expr + Suppress("\\}")
    | expr + Suppress(",") + expr + Suppress(",") + expr + Suppress(",") + expr
)
quad.set_parse_action(lambda t: Quad(values=(t[0], t[1], t[2], t[3])))

interval = (
    Literal("(") + expr + Suppress(",") + expr + Literal("]")
    | Literal("\\left(") + expr + Suppress(",") + expr + Literal("\\right]")
    | Literal("[") + expr + Suppress(",") + expr + Literal("]")
    | Literal("\\left[") + expr + Suppress(",") + expr + Literal("\\right]")
    | Literal("[") + expr + Suppress(",") + expr + Literal(")")
    | Literal("\\left[") + expr + Suppress(",") + expr + Literal("\\right)")
)
interval.set_parse_action(lambda t: Interval(values=(t[1], t[2]), brackets=t[0][-1] + t[3][-1]))

pmtuple = (
    Suppress("(") + expr + Suppress("\\pm") + expr + Suppress(",") + expr + Suppress(")")
    | Suppress("\\left(") + expr + Suppress("\\pm") + expr + Suppress(",") + expr + Suppress("\\right)")
    | Suppress("\\{") + expr + Suppress("\\pm") + expr + Suppress(",") + expr + Suppress("\\}")
    | expr + Suppress("\\pm") + expr + Suppress(",") + expr
)
pmtuple.set_parse_action(lambda t: Tuple(values=(PlusMinus(values=(t[0], t[1])), t[2])))

equation = expr + Suppress("=") + expr
equation.set_parse_action(lambda t: Equation(lh=t[0], rh=t[1]))

pm = expr + Suppress("\\pm") + expr
pm.set_parse_action(lambda t: PlusMinus(values=(t[0], t[1])))

union = Or([interval, tuple_]) + Suppress("\\cup") + Or([interval, tuple_])
union.set_parse_action(lambda t: Union(op1=t[0], op2=t[1]))

everything = matrix | union | pm | equation | pmtuple | quad | triple | tuple_ | interval | expr


def parse(x: str) -> Node | None:
    try:
        result = everything.parse_string(x, parse_all=True)
        return result[0]
    except Exception:
        log.warning(f"Failed to parse expression {x}")
        return None


def pretty(node, indent=0):
    if node.type == "number":
        print("  " * indent + str(node.value))
    elif node.type == "variable":
        print("  " * indent + str(node.name))
    elif node.type == "tuple":
        print("  " * indent + "tuple")
        pretty(node.values[0], indent=indent + 1)
        pretty(node.values[1], indent=indent + 1)
    elif node.type == "interval":
        print("  " * indent + "interval " + node.brackets)
        pretty(node.values[0], indent=indent + 1)
        pretty(node.values[1], indent=indent + 1)
    elif node.type == "triple":
        print("  " * indent + "triple")
        pretty(node.values[0], indent=indent + 1)
        pretty(node.values[1], indent=indent + 1)
        pretty(node.values[2], indent=indent + 1)
    elif node.type == "quad":
        print("  " * indent + "quad")
        pretty(node.values[0], indent=indent + 1)
        pretty(node.values[1], indent=indent + 1)
        pretty(node.values[2], indent=indent + 1)
        pretty(node.values[3], indent=indent + 1)
    elif node.type == "negation":
        print("  " * indent + "negation")
        pretty(node.op, indent=indent + 1)
    elif node.type == "function1":
        print("  " * indent + "function1 " + node.name)
        pretty(node.op1, indent=indent + 1)
    elif node.type == "function2":
        print("  " * indent + "function2 " + node.name)
        pretty(node.op1, indent=indent + 1)
        pretty(node.op2, indent=indent + 1)
    elif node.type == "binary":
        print("  " * indent + "binary " + node.name)
        pretty(node.op1, indent=indent + 1)
        pretty(node.op2, indent=indent + 1)
    elif node.type == "plus-minus":
        print("  " * indent + "plus-minus")
        pretty(node.values[0], indent=indent + 1)
        pretty(node.values[1], indent=indent + 1)
    elif node.type == "text":
        print("  " * indent + "text " + node.text)
    elif node.type == "equation":
        print("  " * indent + "equation")
        pretty(node.lh, indent=indent + 1)
        pretty(node.rh, indent=indent + 1)
    elif node.type == "matrix":
        print("  " * indent + "matrix")
        for row in node.rows:
            for e in row:
                pretty(e, indent=indent + 2)
            print("  " * indent + "  =====")
    else:
        assert False, node
