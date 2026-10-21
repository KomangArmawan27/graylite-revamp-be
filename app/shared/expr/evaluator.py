import re
from typing import Any, Dict
from app.shared.expr.functions import HELPER_FUNCS, MATH_FUNCS

def evaluate_expression(expr: str, context: Dict[str, Any]) -> Any:
    if not expr or not expr.strip():
        return None
    expr_str = expr.strip()
    
    # Simple substitution and evaluation for safe subset (numbers, basic arithmetic, variable names, ISNA, Math)
    # Case-insensitive context keys
    ctx = {k.lower(): v for k, v in context.items()}
    
    # If expr is just a single variable or number or string literal
    if expr_str.lower() in ctx:
        return ctx[expr_str.lower()]
    
    try:
        # Check if it's a numeric literal
        return float(expr_str) if "." in expr_str else int(expr_str)
    except ValueError:
        pass

    if expr_str.startswith("'") and expr_str.endswith("'") or expr_str.startswith('"') and expr_str.endswith('"'):
        return expr_str[1:-1]

    # Handle Math.* and helper functions and basic arithmetic
    # For a safe evaluator without eval, we can parse or evaluate tokens.
    # Let's support safe expression evaluation using Python's ast with strict node whitelisting.
    import ast
    
    class SafeEvaluator(ast.NodeVisitor):
        def visit(self, node):
            if isinstance(node, ast.Expression):
                return self.visit(node.body)
            elif isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Num): # Python < 3.8 compatibility
                return node.n
            elif isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, ast.Name):
                name_lower = node.id.lower()
                if name_lower in ctx:
                    return ctx[name_lower]
                if node.id == "Math":
                    return "MathNamespace"
                raise ValueError(f"Unknown variable: {node.id}")
            elif isinstance(node, ast.Attribute):
                value = self.visit(node.value)
                if value == "MathNamespace" and node.attr.lower() in MATH_FUNCS:
                    return MATH_FUNCS[node.attr.lower()]
                raise AttributeError(f"Invalid attribute: {node.attr}")
            elif isinstance(node, ast.BinOp):
                left = self.visit(node.left)
                right = self.visit(node.right)
                if isinstance(node.op, ast.Add): return left + right
                if isinstance(node.op, ast.Sub): return left - right
                if isinstance(node.op, ast.Mult): return left * right
                if isinstance(node.op, ast.Div): return left / right if right != 0 else 0
                if isinstance(node.op, ast.Mod): return left % right
                raise ValueError("Unsupported operator")
            elif isinstance(node, ast.UnaryOp):
                operand = self.visit(node.operand)
                if isinstance(node.op, ast.USub): return -operand
                if isinstance(node.op, ast.UAdd): return +operand
                raise ValueError("Unsupported unary operator")
            elif isinstance(node, ast.IfExp):
                test = self.visit(node.test)
                return self.visit(node.body) if test else self.visit(node.orelse)
            elif isinstance(node, ast.Compare):
                left = self.visit(node.left)
                for op, comp in zip(node.ops, node.comparators):
                    right = self.visit(comp)
                    if isinstance(op, ast.Eq) and not (left == right): return False
                    if isinstance(op, ast.NotEq) and not (left != right): return False
                    if isinstance(op, ast.Lt) and not (left < right): return False
                    if isinstance(op, ast.LtE) and not (left <= right): return False
                    if isinstance(op, ast.Gt) and not (left > right): return False
                    if isinstance(op, ast.GtE) and not (left >= right): return False
                return True
            elif isinstance(node, ast.Call):
                func = self.visit(node.func)
                args = [self.visit(arg) for arg in node.args]
                if callable(func):
                    return func(*args)
                elif isinstance(func, str) and func.lower() in HELPER_FUNCS:
                    return HELPER_FUNCS[func.lower()](*args)
                raise ValueError(f"Unsupported function call")
            else:
                raise ValueError(f"Unsupported expression construct: {type(node).__name__}")

    try:
        tree = ast.parse(expr_str, mode='eval')
        evaluator = SafeEvaluator()
        return evaluator.visit(tree)
    except Exception:
        return None
