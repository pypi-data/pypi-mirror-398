import re
import secrets
from typing import Dict, Tuple, Optional

from .exceptions import ConditionError


class ConditionEvaluator:
    
    EQUALS_PATTERN = re.compile(r'^(.+?)\s*==\s*"([^"]*)"$')
    EQUALS_PATTERN_UNQUOTED = re.compile(r'^(.+?)\s*==\s*(.+)$')
    NOT_EQUALS_PATTERN = re.compile(r'^(.+?)\s*!=\s*"([^"]*)"$')
    NOT_EQUALS_PATTERN_UNQUOTED = re.compile(r'^(.+?)\s*!=\s*(.+)$')
    DEFINED_PATTERN = re.compile(r'^defined\(([A-Za-z_][A-Za-z0-9_]*)\)$')
    NOT_DEFINED_PATTERN = re.compile(r'^not_defined\(([A-Za-z_][A-Za-z0-9_]*)\)$')
    
    def __init__(self, env: Dict[str, str]):
        self.env = env
    
    def evaluate(self, condition: str, file: str = None, line: int = None) -> bool:
        condition = condition.strip()
        return self._evaluate_expression(condition, file, line)
    
    def _evaluate_expression(self, expr: str, file: str = None, line: int = None) -> bool:
        expr = expr.strip()
        
        while expr.startswith('(') and expr.endswith(')') and self._matching_parens(expr):
            expr = expr[1:-1].strip()
        
        if expr.startswith('NOT '):
            inner = expr[4:].strip()
            return not self._evaluate_expression(inner, file, line)
        
        or_parts = self._split_by_operator(expr, ' OR ')
        if len(or_parts) > 1:
            return any(self._evaluate_expression(part, file, line) for part in or_parts)
        
        and_parts = self._split_by_operator(expr, ' AND ')
        if len(and_parts) > 1:
            return all(self._evaluate_expression(part, file, line) for part in and_parts)
        
        return self._evaluate_comparison(expr, file, line)
    
    def _split_by_operator(self, expr: str, operator: str) -> list:
        parts = []
        current = []
        depth = 0
        i = 0
        
        while i < len(expr):
            if expr[i] == '(':
                depth += 1
                current.append(expr[i])
            elif expr[i] == ')':
                depth -= 1
                current.append(expr[i])
            elif depth == 0 and expr[i:i+len(operator)] == operator:
                parts.append(''.join(current).strip())
                current = []
                i += len(operator) - 1
            else:
                current.append(expr[i])
            i += 1
        
        if current:
            parts.append(''.join(current).strip())
        
        return parts if len(parts) > 1 else [expr]
    
    def _matching_parens(self, expr: str) -> bool:
        if not (expr.startswith('(') and expr.endswith(')')):
            return False
        
        depth = 0
        for i, char in enumerate(expr):
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            if depth == 0 and i < len(expr) - 1:
                return False
        
        return depth == 0
    
    def _evaluate_comparison(self, condition: str, file: str = None, line: int = None) -> bool:
        condition = condition.strip()
        
        while condition.startswith('(') and condition.endswith(')') and self._matching_parens(condition):
            condition = condition[1:-1].strip()
        
        match = self.DEFINED_PATTERN.match(condition)
        if match:
            var = match.group(1)
            return var in self.env
        
        match = self.NOT_DEFINED_PATTERN.match(condition)
        if match:
            var = match.group(1)
            return var not in self.env
        
        match = self.EQUALS_PATTERN.match(condition)
        if match:
            var = match.group(1).strip()
            expected = match.group(2)
            actual = self.env.get(var, "")
            return self._secure_compare(actual, expected)
        
        match = self.EQUALS_PATTERN_UNQUOTED.match(condition)
        if match:
            var = match.group(1).strip()
            expected = match.group(2).strip()
            actual = self.env.get(var, "")
            return self._secure_compare(actual, expected)
        
        match = self.NOT_EQUALS_PATTERN.match(condition)
        if match:
            var = match.group(1).strip()
            expected = match.group(2)
            actual = self.env.get(var, "")
            return not self._secure_compare(actual, expected)
        
        match = self.NOT_EQUALS_PATTERN_UNQUOTED.match(condition)
        if match:
            var = match.group(1).strip()
            expected = match.group(2).strip()
            actual = self.env.get(var, "")
            return not self._secure_compare(actual, expected)
        
        raise ConditionError(f"Invalid condition syntax: {condition}", file, line)
    
    @staticmethod
    def _secure_compare(a: str, b: str) -> bool:
        return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))
