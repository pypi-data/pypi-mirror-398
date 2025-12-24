"""Semantic analysis module for NoCapLang.

This module provides type checking, symbol resolution, and semantic validation.
"""

from .types import (
    Type,
    PrimitiveType,
    ArrayType,
    MapType,
    FunctionType,
    ClassType,
    UnionType,
    TypeVariable,
    TypeUnifier,
    TEXT_TYPE,
    DIGITS_TYPE,
    TF_TYPE,
    VOID_TYPE,
    GHOST_TYPE,
    parse_type_annotation,
)

from .analyzer import (
    SemanticAnalyzer,
    SymbolTable,
    Symbol,
    SemanticError,
)

__all__ = [
    'Type',
    'PrimitiveType',
    'ArrayType',
    'MapType',
    'FunctionType',
    'ClassType',
    'UnionType',
    'TypeVariable',
    'TypeUnifier',
    'TEXT_TYPE',
    'DIGITS_TYPE',
    'TF_TYPE',
    'VOID_TYPE',
    'GHOST_TYPE',
    'parse_type_annotation',
    'SemanticAnalyzer',
    'SymbolTable',
    'Symbol',
    'SemanticError',
]
