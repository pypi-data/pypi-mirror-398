from pprint import pprint
from dataclasses import dataclass
from typing import Any
import re
from .exceptions import InvalidExpression, NotFound
from decimal import Decimal, localcontext
from .finals import DEFAULT_ROUNDING

class SafeExpression(str):
    """
    A string subclass that validates it contains only safe mathematical characters.
    """
    
    VALID_CHARS = set("0123456789.+-*/%() ")
    
    def __new__(cls, expr: str):
        # Validate before creating the instance
        if not isinstance(expr, str):
            raise InvalidExpression("Expression must be a string")
        
        invalid_chars = set(expr) - cls.VALID_CHARS
        if invalid_chars:
            chars = list(invalid_chars)[:3]
            examples = ', '.join([f"'{c}'" for c in chars])
            label = str(expr[:64]+" [...]").strip() if len(expr) > 64 else expr
            raise InvalidExpression(f"'{label}' is not a valid expression. Characters such as {examples} are not allowed.")
        
        # Create and return the string instance
        return super().__new__(cls, expr.strip())

@dataclass
class Sheet:
    def __init__(self) -> None:
        self.stats = {}

    def get_all_stats(self):
        return self.stats
        
    def get_stat(self, id: str):
        return self.stats.get(id)
        
    def add_stats(self, stats_dict: dict[str, str]):
        for id, expr in stats_dict.items():
            self.stats.update({id: expr})
            
    def del_stats(self, ids: list[str]):
        for id in ids:
            self.stats.pop(id)
    
    def solve_expressions(self, ns_censuses: dict[int, Any] = None, rounding = DEFAULT_ROUNDING):
        if ns_censuses and not isinstance(ns_censuses, dict):
            raise TypeError(f"ns_censuses must be a dictionary, not {type(ns_censuses).__name__}")
        all_stats = self.get_all_stats()
        solved_sheet = {}
        
        def parse_brackets(expr: str):
            def parse_match(match: str):
                replacement = ns_censuses[int(match.group(1))]
                return replacement
            pattern = r"(\[(\d+)\])"
            new_expr = re.sub(pattern, parse_match, expr)
            return new_expr
        def parse_existing_stats(expr: str):
            def parse_match(match: str):
                stat_name = match.group(0)
                replacement = all_stats.get(stat_name)
                if replacement == None:
                    raise NotFound(f"Couldn't parse '{expr}', '{stat_name}' not found")
                return parse_existing_stats(replacement)
            pattern = r"[a-z_A-Z]+"
            new_expr = re.sub(pattern, parse_match, expr)
            return new_expr
                
        def evaluate_expression(expr: str) -> Any:
            safe_expr = SafeExpression(expr)
            def numbers_to_decimals(x: str):
                def parse_match(match: str):
                    return f"Decimal('{match.group(0)}')"
                pattern = r'-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
                new_string = re.sub(pattern, parse_match, x)
                return new_string
            with localcontext() as local_context:
                safe_globals = {"__builtins__": {}}
                safe_locals = {"Decimal": Decimal}
                local_context.prec = 28
                local_context.rounding = rounding
                parsed_numbers = numbers_to_decimals(safe_expr)
                return eval(parsed_numbers, safe_globals, safe_locals)
        def parse_expr(expr: str):
            if not isinstance(expr, str):
                raise TypeError(f"expressions must be strings, but '{expr}' is {type(expr).__name__}")
            parsed_existing_stats = parse_existing_stats(expr)
            parsed_brackets = parse_brackets(parsed_existing_stats)
            expr_result = evaluate_expression(parsed_brackets)
            return expr_result
        
        for id, expr in all_stats.items():
            parsed = parse_expr(expr)
            solved_sheet.update({id: str(parsed)})
        return solved_sheet
    
if __name__ == "__main__":
    pass