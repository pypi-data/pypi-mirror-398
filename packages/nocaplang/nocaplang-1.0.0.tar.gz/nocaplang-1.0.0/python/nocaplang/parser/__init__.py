"""Parser module for NoCapLang."""

from .parser import Parser, ParseError
from .ast_nodes import (
    # Base classes
    Node,
    ExpressionNode,
    StatementNode,
    
    # Program structure
    ProgramNode,
    ImportNode,
    
    # Literals
    LiteralNode,
    ArrayLiteralNode,
    ObjectLiteralNode,
    
    # Variables and identifiers
    IdentifierNode,
    
    # Operators
    BinaryOpNode,
    UnaryOpNode,
    
    # Calls and access
    CallNode,
    IndexNode,
    MemberAccessNode,
    
    # Lambda and async
    LambdaNode,
    AwaitNode,
    NewNode,
    
    # Declarations
    VariableDeclarationNode,
    FunctionDeclarationNode,
    ClassDeclarationNode,
    EnumDeclarationNode,
    
    # Assignments and expressions
    AssignmentNode,
    ExpressionStatementNode,
    PrintStatementNode,
    
    # Control flow
    IfStatementNode,
    ForLoopNode,
    WhileLoopNode,
    ForEachLoopNode,
    ReturnStatementNode,
    BreakStatementNode,
    ContinueStatementNode,
    
    # Error handling
    TryStatementNode,
    ThrowStatementNode,
    AssertStatementNode,
    
    # Pattern matching
    CaseNode,
    MatchStatementNode,
    
    # Type annotations
    TypeAnnotation,
)

__all__ = [
    # Parser
    'Parser',
    'ParseError',
    
    # Base classes
    'Node',
    'ExpressionNode',
    'StatementNode',
    
    # Program structure
    'ProgramNode',
    'ImportNode',
    
    # Literals
    'LiteralNode',
    'ArrayLiteralNode',
    'ObjectLiteralNode',
    
    # Variables and identifiers
    'IdentifierNode',
    
    # Operators
    'BinaryOpNode',
    'UnaryOpNode',
    
    # Calls and access
    'CallNode',
    'IndexNode',
    'MemberAccessNode',
    
    # Lambda and async
    'LambdaNode',
    'AwaitNode',
    'NewNode',
    
    # Declarations
    'VariableDeclarationNode',
    'FunctionDeclarationNode',
    'ClassDeclarationNode',
    'EnumDeclarationNode',
    
    # Assignments and expressions
    'AssignmentNode',
    'ExpressionStatementNode',
    'PrintStatementNode',
    
    # Control flow
    'IfStatementNode',
    'ForLoopNode',
    'WhileLoopNode',
    'ForEachLoopNode',
    'ReturnStatementNode',
    'BreakStatementNode',
    'ContinueStatementNode',
    
    # Error handling
    'TryStatementNode',
    'ThrowStatementNode',
    'AssertStatementNode',
    
    # Pattern matching
    'CaseNode',
    'MatchStatementNode',
    
    # Type annotations
    'TypeAnnotation',
]
