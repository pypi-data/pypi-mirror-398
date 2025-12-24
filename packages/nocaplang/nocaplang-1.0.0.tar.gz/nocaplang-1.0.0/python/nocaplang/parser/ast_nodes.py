"""Abstract Syntax Tree node definitions for NoCapLang parser."""

from dataclasses import dataclass
from typing import Any, Optional, List
from abc import ABC, abstractmethod
from ..lexer.token import Position


# ============================================================================
# Base Node Classes
# ============================================================================

class Node(ABC):
    """Base class for all AST nodes."""
    
    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor for the visitor pattern."""
        pass


class ExpressionNode(Node):
    """Base class for all expression nodes."""
    
    @abstractmethod
    def accept(self, visitor):
        pass


class StatementNode(Node):
    """Base class for all statement nodes."""
    
    @abstractmethod
    def accept(self, visitor):
        pass


# ============================================================================
# Program Structure
# ============================================================================

@dataclass
class ProgramNode(Node):
    """Root node containing the entire program."""
    position: Position
    statements: List[StatementNode]
    
    def accept(self, visitor):
        return visitor.visit_program(self)


@dataclass
class ImportNode(StatementNode):
    """Represents a 'grab' import statement."""
    position: Position
    path: str
    symbols: Optional[List[str]] = None  # None means import all
    
    def accept(self, visitor):
        return visitor.visit_import(self)


# ============================================================================
# Literal Expressions
# ============================================================================

@dataclass
class LiteralNode(ExpressionNode):
    """Represents a literal value (number, string, boolean, null)."""
    position: Position
    value: Any
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_literal(self)


@dataclass
class ArrayLiteralNode(ExpressionNode):
    """Represents a lineup (array) literal."""
    position: Position
    elements: List[ExpressionNode]
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_array_literal(self)


@dataclass
class ObjectLiteralNode(ExpressionNode):
    """Represents a bag (object/dictionary) literal."""
    position: Position
    pairs: List[tuple[ExpressionNode, ExpressionNode]]  # (key, value) pairs
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_object_literal(self)


# ============================================================================
# Variable and Identifier Expressions
# ============================================================================

@dataclass
class IdentifierNode(ExpressionNode):
    """Represents a variable or function reference."""
    position: Position
    name: str
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_identifier(self)


# ============================================================================
# Operator Expressions
# ============================================================================

@dataclass
class BinaryOpNode(ExpressionNode):
    """Represents a binary operation (e.g., a + b, a == b)."""
    position: Position
    left: ExpressionNode
    operator: str
    right: ExpressionNode
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_binary_op(self)


@dataclass
class UnaryOpNode(ExpressionNode):
    """Represents a unary operation (e.g., -x, not x)."""
    position: Position
    operator: str
    operand: ExpressionNode
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_unary_op(self)


# ============================================================================
# Call and Access Expressions
# ============================================================================

@dataclass
class CallNode(ExpressionNode):
    """Represents a function call."""
    position: Position
    callee: ExpressionNode
    arguments: List[ExpressionNode]
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_call(self)


@dataclass
class IndexNode(ExpressionNode):
    """Represents array/object indexing (e.g., arr[0], obj[key])."""
    position: Position
    object: ExpressionNode
    index: ExpressionNode
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_index(self)


@dataclass
class MemberAccessNode(ExpressionNode):
    """Represents object property access (e.g., obj.property)."""
    position: Position
    object: ExpressionNode
    member: str
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_member_access(self)


# ============================================================================
# Lambda and Async Expressions
# ============================================================================

@dataclass
class LambdaNode(ExpressionNode):
    """Represents an anonymous function."""
    position: Position
    parameters: List[tuple[str, Optional[str]]]  # (name, type_annotation)
    body: List[StatementNode]
    return_type: Optional[str] = None
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_lambda(self)


@dataclass
class AwaitNode(ExpressionNode):
    """Represents a 'holdup' (await) expression."""
    position: Position
    expression: ExpressionNode
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_await(self)


@dataclass
class NewNode(ExpressionNode):
    """Represents class instantiation."""
    position: Position
    class_name: str
    arguments: List[ExpressionNode]
    expr_type: Optional[Any] = None
    
    def accept(self, visitor):
        return visitor.visit_new(self)


# ============================================================================
# Declaration Statements
# ============================================================================

@dataclass
class VariableDeclarationNode(StatementNode):
    """Represents a 'fr' variable declaration."""
    position: Position
    name: str
    type_annotation: Optional[str] = None
    initializer: Optional[ExpressionNode] = None
    
    def accept(self, visitor):
        return visitor.visit_variable_declaration(self)


@dataclass
class FunctionDeclarationNode(StatementNode):
    """Represents a 'lowkey' function declaration."""
    position: Position
    name: str
    parameters: List[tuple[str, Optional[str]]]  # (name, type_annotation)
    body: List[StatementNode]
    return_type: Optional[str] = None
    is_async: bool = False  # True if declared with 'chill'
    
    def accept(self, visitor):
        return visitor.visit_function_declaration(self)


@dataclass
class ClassDeclarationNode(StatementNode):
    """Represents a 'vibe' class declaration."""
    position: Position
    name: str
    parent: Optional[str] = None  # Parent class name (vibes_with)
    fields: List[VariableDeclarationNode] = None
    methods: List[FunctionDeclarationNode] = None
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = []
        if self.methods is None:
            self.methods = []
    
    def accept(self, visitor):
        return visitor.visit_class_declaration(self)


@dataclass
class EnumDeclarationNode(StatementNode):
    """Represents a 'choices' enum declaration."""
    position: Position
    name: str
    values: List[str]
    
    def accept(self, visitor):
        return visitor.visit_enum_declaration(self)


# ============================================================================
# Assignment and Expression Statements
# ============================================================================

@dataclass
class AssignmentNode(StatementNode):
    """Represents an assignment statement."""
    position: Position
    target: ExpressionNode  # Can be identifier, index, or member access
    value: ExpressionNode
    
    def accept(self, visitor):
        return visitor.visit_assignment(self)


@dataclass
class ExpressionStatementNode(StatementNode):
    """Represents an expression used as a statement."""
    position: Position
    expression: ExpressionNode
    
    def accept(self, visitor):
        return visitor.visit_expression_statement(self)


@dataclass
class PrintStatementNode(StatementNode):
    """Represents a 'yap' print statement."""
    position: Position
    arguments: List[ExpressionNode]
    
    def accept(self, visitor):
        return visitor.visit_print_statement(self)


# ============================================================================
# Control Flow Statements
# ============================================================================

@dataclass
class IfStatementNode(StatementNode):
    """Represents a 'vibecheck' (if) statement."""
    position: Position
    condition: ExpressionNode
    then_branch: List[StatementNode]
    elif_branches: List[tuple[ExpressionNode, List[StatementNode]]] = None
    else_branch: Optional[List[StatementNode]] = None
    
    def __post_init__(self):
        if self.elif_branches is None:
            self.elif_branches = []
    
    def accept(self, visitor):
        return visitor.visit_if_statement(self)


@dataclass
class ForLoopNode(StatementNode):
    """Represents a 'run' (for) loop."""
    position: Position
    initializer: Optional[StatementNode]
    condition: Optional[ExpressionNode]
    increment: Optional[ExpressionNode]
    body: List[StatementNode]
    
    def accept(self, visitor):
        return visitor.visit_for_loop(self)


@dataclass
class WhileLoopNode(StatementNode):
    """Represents an 'until' (while) loop."""
    position: Position
    condition: ExpressionNode
    body: List[StatementNode]
    
    def accept(self, visitor):
        return visitor.visit_while_loop(self)


@dataclass
class ForEachLoopNode(StatementNode):
    """Represents an 'each' (for-each) loop."""
    position: Position
    variable: str
    key_variable: Optional[str] = None  # For iterating over bags with key
    iterable: ExpressionNode = None
    body: List[StatementNode] = None
    
    def __post_init__(self):
        if self.body is None:
            self.body = []
    
    def accept(self, visitor):
        return visitor.visit_foreach_loop(self)


@dataclass
class ReturnStatementNode(StatementNode):
    """Represents a 'comeback' (return) statement."""
    position: Position
    value: Optional[ExpressionNode] = None
    
    def accept(self, visitor):
        return visitor.visit_return_statement(self)


@dataclass
class BreakStatementNode(StatementNode):
    """Represents a 'dip' (break) statement."""
    position: Position
    
    def accept(self, visitor):
        return visitor.visit_break_statement(self)


@dataclass
class ContinueStatementNode(StatementNode):
    """Represents a 'skip' (continue) statement."""
    position: Position
    
    def accept(self, visitor):
        return visitor.visit_continue_statement(self)


# ============================================================================
# Error Handling Statements
# ============================================================================

@dataclass
class TryStatementNode(StatementNode):
    """Represents a 'tryna' (try-catch-finally) statement."""
    position: Position
    try_block: List[StatementNode]
    catch_variable: Optional[str] = None
    catch_block: Optional[List[StatementNode]] = None
    finally_block: Optional[List[StatementNode]] = None
    
    def accept(self, visitor):
        return visitor.visit_try_statement(self)


@dataclass
class ThrowStatementNode(StatementNode):
    """Represents a 'crash' (throw) statement."""
    position: Position
    expression: ExpressionNode
    
    def accept(self, visitor):
        return visitor.visit_throw_statement(self)


@dataclass
class AssertStatementNode(StatementNode):
    """Represents a 'nocap' (assert) statement."""
    position: Position
    condition: ExpressionNode
    message: Optional[ExpressionNode] = None
    
    def accept(self, visitor):
        return visitor.visit_assert_statement(self)


# ============================================================================
# Pattern Matching
# ============================================================================

@dataclass
class CaseNode(Node):
    """Represents a single case in a match statement."""
    position: Position
    pattern: ExpressionNode  # Can be literal, type check, or range
    guard: Optional[ExpressionNode] = None  # Optional condition
    body: List[StatementNode] = None
    
    def __post_init__(self):
        if self.body is None:
            self.body = []
    
    def accept(self, visitor):
        return visitor.visit_case(self)


@dataclass
class MatchStatementNode(StatementNode):
    """Represents a 'match' (pattern matching) statement."""
    position: Position
    expression: ExpressionNode
    cases: List[CaseNode]
    default_case: Optional[List[StatementNode]] = None
    
    def accept(self, visitor):
        return visitor.visit_match_statement(self)


# ============================================================================
# Type Annotation Support
# ============================================================================

@dataclass
class TypeAnnotation:
    """Represents a type annotation."""
    name: str  # Base type name (text, digits, tf, lineup, bag, etc.)
    generic_params: Optional[List['TypeAnnotation']] = None  # For lineup<T>, bag<K,V>
    position: Optional[Position] = None
    
    def __str__(self) -> str:
        if self.generic_params:
            params = ', '.join(str(p) for p in self.generic_params)
            return f"{self.name}<{params}>"
        return self.name
