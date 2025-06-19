"""Calculator tool for mathematical operations"""
import ast
import operator
import math

TOOL_NAME = "calculator"
TOOL_DESCRIPTION = "Perform basic mathematical calculations safely"

# Supported operators for safe evaluation
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.USub: operator.neg,
}

# Supported functions
FUNCTIONS = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'pi': math.pi,
    'e': math.e,
}

def safe_eval(node):
    """Safely evaluate mathematical expressions"""
    if isinstance(node, ast.Constant):  # Python 3.8+
        return node.value
    elif isinstance(node, ast.Num):  # Python < 3.8
        return node.n
    elif isinstance(node, ast.BinOp):
        return OPERATORS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        return OPERATORS[type(node.op)](safe_eval(node.operand))
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS:
            args = [safe_eval(arg) for arg in node.args]
            return FUNCTIONS[node.func.id](*args)
        else:
            raise ValueError(f"Function {node.func.id} not allowed")
    elif isinstance(node, ast.Name):
        if node.id in FUNCTIONS:
            return FUNCTIONS[node.id]
        else:
            raise ValueError(f"Variable {node.id} not allowed")
    else:
        raise ValueError(f"Operation {type(node)} not allowed")

async def tool_function(expression: str) -> str:
    """Calculate mathematical expression safely"""
    try:
        # Clean the expression
        expression = expression.strip()
        
        if not expression:
            return "❌ Error: Empty expression"
        
        # Parse the expression into an AST
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            return f"❌ Syntax Error: {str(e)}"
        
        # Safely evaluate the expression
        result = safe_eval(tree.body)
        
        # Format the result nicely
        if isinstance(result, float):
            if result.is_integer():
                result = int(result)
            else:
                result = round(result, 10)  # Limit decimal places
        
        return f"📊 Result: {expression} = {result}"
        
    except ZeroDivisionError:
        return "❌ Error: Division by zero"
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except OverflowError:
        return "❌ Error: Number too large"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"