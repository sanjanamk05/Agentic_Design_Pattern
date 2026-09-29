import ast
import math
import operator


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_MAX_EXPRESSION_LENGTH = 256
_MAX_AST_NODES = 64
_MAX_ABS_VALUE = 10**100
_MAX_EXPONENT = 100


def _evaluate(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)

    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT:
            raise ValueError("Exponent is too large.")
        return _BINARY_OPERATORS[type(node.op)](left, right)

    raise ValueError("Only numeric arithmetic expressions are supported.")


def calculator(expression: str) -> str:
    if not expression or len(expression) > _MAX_EXPRESSION_LENGTH:
        raise ValueError("Expression is empty or too long.")

    try:
        syntax = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(syntax)) > _MAX_AST_NODES:
            raise ValueError("Expression is too complex.")
        result = _evaluate(syntax)
    except (SyntaxError, ArithmeticError, OverflowError) as error:
        raise ValueError("Expression could not be evaluated.") from error

    if isinstance(result, complex) or abs(result) > _MAX_ABS_VALUE:
        raise ValueError("Result is outside the supported range.")
    if isinstance(result, float) and not math.isfinite(result):
        raise ValueError("Result is not finite.")

    return str(result)