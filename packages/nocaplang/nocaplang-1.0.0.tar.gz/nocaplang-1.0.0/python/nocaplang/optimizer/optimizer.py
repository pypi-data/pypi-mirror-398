"""AST optimization passes for NoCapLang.

This module implements various optimization passes that preserve program semantics:
- Constant folding: Evaluate constant expressions at compile time
- Dead code elimination: Remove unreachable code
- Target-specific optimizations: Add hints for C++ and Java compilers
"""

from typing import List, Optional, Set
from ..parser.ast_nodes import *
from ..semantic.types import *


class Optimizer:
    """Performs optimization passes on NoCapLang AST."""
    
    def __init__(self, ast: ProgramNode, target: str = "cpp"):
        """Initialize the optimizer.
        
        Args:
            ast: The AST to optimize
            target: Target language ("cpp" or "java")
        """
        self.ast = ast
        self.target = target
        self.optimizations_applied = []
        
    def optimize(self) -> ProgramNode:
        """Apply all optimization passes to the AST.
        
        Returns:
            Optimized AST
        """
        # Apply optimization passes in order
        self.ast = self._constant_folding(self.ast)
        self.ast = self._dead_code_elimination(self.ast)
        self.ast = self._target_specific_optimizations(self.ast)
        
        return self.ast
    
    def get_optimizations_applied(self) -> List[str]:
        """Get list of optimizations that were applied.
        
        Returns:
            List of optimization names
        """
        return self.optimizations_applied
    
    # ========================================================================
    # Constant Folding
    # ========================================================================
    
    def _constant_folding(self, node):
        """Fold constant expressions at compile time.
        
        This optimization evaluates expressions with constant operands
        and replaces them with their computed values.
        """
        if isinstance(node, ProgramNode):
            node.statements = [self._constant_folding(stmt) for stmt in node.statements]
            return node
        
        elif isinstance(node, BinaryOpNode):
            # Recursively fold operands
            node.left = self._constant_folding(node.left)
            node.right = self._constant_folding(node.right)
            
            # Check if both operands are literals
            if isinstance(node.left, LiteralNode) and isinstance(node.right, LiteralNode):
                left_val = node.left.value
                right_val = node.right.value
                
                # Perform constant folding based on operator
                try:
                    result = self._evaluate_binary_op(node.operator, left_val, right_val)
                    if result is not None:
                        self.optimizations_applied.append(f"constant_folding: {left_val} {node.operator} {right_val} -> {result}")
                        # Create new literal node with same position (position, value)
                        new_node = LiteralNode(node.position, result)
                        # Preserve type information if available
                        if hasattr(node, 'expr_type'):
                            new_node.expr_type = node.expr_type
                        return new_node
                except:
                    # If evaluation fails, return original node
                    pass
            
            return node
        
        elif isinstance(node, UnaryOpNode):
            # Recursively fold operand
            node.operand = self._constant_folding(node.operand)
            
            # Check if operand is a literal
            if isinstance(node.operand, LiteralNode):
                operand_val = node.operand.value
                
                try:
                    result = self._evaluate_unary_op(node.operator, operand_val)
                    if result is not None:
                        self.optimizations_applied.append(f"constant_folding: {node.operator}{operand_val} -> {result}")
                        # Create new literal node with same position (position, value)
                        new_node = LiteralNode(node.position, result)
                        # Preserve type information if available
                        if hasattr(node, 'expr_type'):
                            new_node.expr_type = node.expr_type
                        return new_node
                except:
                    pass
            
            return node
        
        elif isinstance(node, IfStatementNode):
            # Fold condition
            node.condition = self._constant_folding(node.condition)
            
            # Fold branches
            node.then_branch = [self._constant_folding(stmt) for stmt in node.then_branch]
            node.elif_branches = [(self._constant_folding(cond), [self._constant_folding(stmt) for stmt in body]) 
                                   for cond, body in node.elif_branches]
            if node.else_branch:
                node.else_branch = [self._constant_folding(stmt) for stmt in node.else_branch]
            
            return node
        
        elif isinstance(node, WhileLoopNode):
            node.condition = self._constant_folding(node.condition)
            node.body = [self._constant_folding(stmt) for stmt in node.body]
            return node
        
        elif isinstance(node, ForLoopNode):
            if node.initializer:
                node.initializer = self._constant_folding(node.initializer)
            if node.condition:
                node.condition = self._constant_folding(node.condition)
            if node.increment:
                node.increment = self._constant_folding(node.increment)
            node.body = [self._constant_folding(stmt) for stmt in node.body]
            return node
        
        elif isinstance(node, ForEachLoopNode):
            node.iterable = self._constant_folding(node.iterable)
            node.body = [self._constant_folding(stmt) for stmt in node.body]
            return node
        
        elif isinstance(node, ReturnStatementNode):
            if node.value:
                node.value = self._constant_folding(node.value)
            return node
        
        elif isinstance(node, VariableDeclarationNode):
            if node.initializer:
                node.initializer = self._constant_folding(node.initializer)
            return node
        
        elif isinstance(node, AssignmentNode):
            node.value = self._constant_folding(node.value)
            return node
        
        elif isinstance(node, ExpressionStatementNode):
            node.expression = self._constant_folding(node.expression)
            return node
        
        elif isinstance(node, PrintStatementNode):
            node.arguments = [self._constant_folding(arg) for arg in node.arguments]
            return node
        
        elif isinstance(node, FunctionDeclarationNode):
            node.body = [self._constant_folding(stmt) for stmt in node.body]
            return node
        
        elif isinstance(node, ClassDeclarationNode):
            node.fields = [self._constant_folding(field) for field in node.fields]
            node.methods = [self._constant_folding(method) for method in node.methods]
            return node
        
        elif isinstance(node, TryStatementNode):
            node.try_block = [self._constant_folding(stmt) for stmt in node.try_block]
            if node.catch_block:
                node.catch_block = [self._constant_folding(stmt) for stmt in node.catch_block]
            if node.finally_block:
                node.finally_block = [self._constant_folding(stmt) for stmt in node.finally_block]
            return node
        
        elif isinstance(node, ThrowStatementNode):
            node.expression = self._constant_folding(node.expression)
            return node
        
        elif isinstance(node, AssertStatementNode):
            node.condition = self._constant_folding(node.condition)
            if node.message:
                node.message = self._constant_folding(node.message)
            return node
        
        elif isinstance(node, MatchStatementNode):
            node.expression = self._constant_folding(node.expression)
            for case in node.cases:
                case.pattern = self._constant_folding(case.pattern)
                if case.guard:
                    case.guard = self._constant_folding(case.guard)
                case.body = [self._constant_folding(stmt) for stmt in case.body]
            if node.default_case:
                node.default_case = [self._constant_folding(stmt) for stmt in node.default_case]
            return node
        
        elif isinstance(node, CallNode):
            node.callee = self._constant_folding(node.callee)
            node.arguments = [self._constant_folding(arg) for arg in node.arguments]
            return node
        
        elif isinstance(node, IndexNode):
            node.object = self._constant_folding(node.object)
            node.index = self._constant_folding(node.index)
            return node
        
        elif isinstance(node, MemberAccessNode):
            node.object = self._constant_folding(node.object)
            return node
        
        elif isinstance(node, ArrayLiteralNode):
            node.elements = [self._constant_folding(elem) for elem in node.elements]
            return node
        
        elif isinstance(node, ObjectLiteralNode):
            node.pairs = [(self._constant_folding(k), self._constant_folding(v)) for k, v in node.pairs]
            return node
        
        elif isinstance(node, LambdaNode):
            node.body = [self._constant_folding(stmt) for stmt in node.body]
            return node
        
        elif isinstance(node, AwaitNode):
            node.expression = self._constant_folding(node.expression)
            return node
        
        elif isinstance(node, NewNode):
            node.arguments = [self._constant_folding(arg) for arg in node.arguments]
            return node
        
        # Return node unchanged if no optimization applies
        return node
    
    def _evaluate_binary_op(self, operator: str, left, right):
        """Evaluate a binary operation on constant values."""
        if operator == "+":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            elif isinstance(left, str) and isinstance(right, str):
                return left + right
        elif operator == "-":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left - right
        elif operator == "*":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left * right
        elif operator == "/":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)) and right != 0:
                return left / right
        elif operator == "%":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)) and right != 0:
                return left % right
        elif operator == "==":
            return left == right
        elif operator == "!=":
            return left != right
        elif operator == "<":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left < right
        elif operator == ">":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left > right
        elif operator == "<=":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left <= right
        elif operator == ">=":
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left >= right
        elif operator == "and":
            if isinstance(left, bool) and isinstance(right, bool):
                return left and right
        elif operator == "or":
            if isinstance(left, bool) and isinstance(right, bool):
                return left or right
        
        return None
    
    def _evaluate_unary_op(self, operator: str, operand):
        """Evaluate a unary operation on a constant value."""
        if operator == "-":
            if isinstance(operand, (int, float)):
                return -operand
        elif operator == "+":
            if isinstance(operand, (int, float)):
                return +operand
        elif operator == "not":
            if isinstance(operand, bool):
                return not operand
        
        return None
    
    # ========================================================================
    # Dead Code Elimination
    # ========================================================================
    
    def _dead_code_elimination(self, node):
        """Remove unreachable code.
        
        This optimization removes code that can never be executed:
        - Code after return statements
        - Code in branches with constant false conditions
        """
        if isinstance(node, ProgramNode):
            node.statements = self._eliminate_dead_statements(node.statements)
            return node
        
        elif isinstance(node, IfStatementNode):
            # Check if condition is a constant
            if isinstance(node.condition, LiteralNode):
                if node.condition.value:
                    # Condition is always true, replace with then branch
                    self.optimizations_applied.append("dead_code_elimination: removed always-false branches")
                    return self._eliminate_dead_statements(node.then_branch)
                else:
                    # Condition is always false, check elif/else
                    for elif_cond, elif_body in node.elif_branches:
                        if isinstance(elif_cond, LiteralNode) and elif_cond.value:
                            return self._eliminate_dead_statements(elif_body)
                    
                    if node.else_branch:
                        return self._eliminate_dead_statements(node.else_branch)
                    else:
                        # Entire if statement is dead
                        self.optimizations_applied.append("dead_code_elimination: removed always-false if statement")
                        return []
            
            # Recursively process branches
            node.then_branch = self._eliminate_dead_statements(node.then_branch)
            node.elif_branches = [(cond, self._eliminate_dead_statements(body)) for cond, body in node.elif_branches]
            if node.else_branch:
                node.else_branch = self._eliminate_dead_statements(node.else_branch)
            
            return node
        
        elif isinstance(node, WhileLoopNode):
            # Check for infinite loops with constant true condition
            if isinstance(node.condition, LiteralNode) and not node.condition.value:
                # Loop never executes
                self.optimizations_applied.append("dead_code_elimination: removed never-executing while loop")
                return []
            
            node.body = self._eliminate_dead_statements(node.body)
            return node
        
        elif isinstance(node, ForLoopNode):
            if node.initializer:
                node.initializer = self._dead_code_elimination(node.initializer)
            node.body = self._eliminate_dead_statements(node.body)
            return node
        
        elif isinstance(node, ForEachLoopNode):
            node.body = self._eliminate_dead_statements(node.body)
            return node
        
        elif isinstance(node, FunctionDeclarationNode):
            node.body = self._eliminate_dead_statements(node.body)
            return node
        
        elif isinstance(node, ClassDeclarationNode):
            node.methods = [self._dead_code_elimination(method) for method in node.methods]
            return node
        
        elif isinstance(node, TryStatementNode):
            node.try_block = self._eliminate_dead_statements(node.try_block)
            if node.catch_block:
                node.catch_block = self._eliminate_dead_statements(node.catch_block)
            if node.finally_block:
                node.finally_block = self._eliminate_dead_statements(node.finally_block)
            return node
        
        elif isinstance(node, MatchStatementNode):
            for case in node.cases:
                case.body = self._eliminate_dead_statements(case.body)
            if node.default_case:
                node.default_case = self._eliminate_dead_statements(node.default_case)
            return node
        
        # Return node unchanged
        return node
    
    def _eliminate_dead_statements(self, statements: List) -> List:
        """Remove statements after return/break/continue."""
        result = []
        for i, stmt in enumerate(statements):
            # Process the statement
            processed = self._dead_code_elimination(stmt)
            
            # Handle case where dead code elimination returns a list
            if isinstance(processed, list):
                result.extend(processed)
            else:
                result.append(processed)
            
            # Check if this is a terminal statement
            if isinstance(stmt, (ReturnStatementNode, BreakStatementNode, ContinueStatementNode, ThrowStatementNode)):
                # Remove all statements after this one
                if i < len(statements) - 1:
                    self.optimizations_applied.append(f"dead_code_elimination: removed {len(statements) - i - 1} unreachable statements")
                break
        
        return result
    
    # ========================================================================
    # Target-Specific Optimizations
    # ========================================================================
    
    def _target_specific_optimizations(self, node):
        """Apply target-specific optimization hints.
        
        For C++: Add inline hints, const qualifiers
        For Java: Add final keywords where appropriate
        """
        if self.target == "cpp":
            return self._cpp_optimizations(node)
        elif self.target == "java":
            return self._java_optimizations(node)
        
        return node
    
    def _cpp_optimizations(self, node):
        """Apply C++-specific optimizations."""
        if isinstance(node, ProgramNode):
            node.statements = [self._cpp_optimizations(stmt) for stmt in node.statements]
            return node
        
        elif isinstance(node, FunctionDeclarationNode):
            # Mark small functions for inlining
            if len(node.body) <= 3:  # Small function heuristic
                if not hasattr(node, 'cpp_hints'):
                    node.cpp_hints = []
                node.cpp_hints.append('inline')
                self.optimizations_applied.append(f"cpp_optimization: marked function '{node.name}' as inline")
            
            node.body = [self._cpp_optimizations(stmt) for stmt in node.body]
            return node
        
        elif isinstance(node, VariableDeclarationNode):
            # Mark variables that are never reassigned as const
            # This would require data flow analysis, so we'll skip for now
            if node.initializer:
                node.initializer = self._cpp_optimizations(node.initializer)
            return node
        
        elif isinstance(node, ClassDeclarationNode):
            node.methods = [self._cpp_optimizations(method) for method in node.methods]
            return node
        
        # Recursively process other nodes
        return self._apply_to_children(node, self._cpp_optimizations)
    
    def _java_optimizations(self, node):
        """Apply Java-specific optimizations."""
        if isinstance(node, ProgramNode):
            node.statements = [self._java_optimizations(stmt) for stmt in node.statements]
            return node
        
        elif isinstance(node, VariableDeclarationNode):
            # Mark variables that are never reassigned as final
            # This would require data flow analysis, so we'll mark simple cases
            if node.initializer and isinstance(node.initializer, LiteralNode):
                if not hasattr(node, 'java_hints'):
                    node.java_hints = []
                node.java_hints.append('final')
                self.optimizations_applied.append(f"java_optimization: marked variable '{node.name}' as final")
            
            if node.initializer:
                node.initializer = self._java_optimizations(node.initializer)
            return node
        
        elif isinstance(node, FunctionDeclarationNode):
            node.body = [self._java_optimizations(stmt) for stmt in node.body]
            return node
        
        elif isinstance(node, ClassDeclarationNode):
            node.methods = [self._java_optimizations(method) for method in node.methods]
            return node
        
        # Recursively process other nodes
        return self._apply_to_children(node, self._java_optimizations)
    
    def _apply_to_children(self, node, func):
        """Helper to recursively apply a function to child nodes."""
        if isinstance(node, IfStatementNode):
            node.then_branch = [func(stmt) for stmt in node.then_branch]
            node.elif_branches = [(func(cond), [func(stmt) for stmt in body]) for cond, body in node.elif_branches]
            if node.else_branch:
                node.else_branch = [func(stmt) for stmt in node.else_branch]
        elif isinstance(node, (WhileLoopNode, ForLoopNode, ForEachLoopNode)):
            node.body = [func(stmt) for stmt in node.body]
        elif isinstance(node, TryStatementNode):
            node.try_block = [func(stmt) for stmt in node.try_block]
            if node.catch_block:
                node.catch_block = [func(stmt) for stmt in node.catch_block]
            if node.finally_block:
                node.finally_block = [func(stmt) for stmt in node.finally_block]
        elif isinstance(node, MatchStatementNode):
            for case in node.cases:
                case.body = [func(stmt) for stmt in case.body]
            if node.default_case:
                node.default_case = [func(stmt) for stmt in node.default_case]
        
        return node
