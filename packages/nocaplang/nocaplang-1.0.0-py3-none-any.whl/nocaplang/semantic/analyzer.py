"""Semantic analyzer for NoCapLang.

This module implements semantic analysis including:
- Symbol table management and scope resolution
- Type checking for expressions and statements
- Control flow validation
- Undefined variable detection with suggestions
- Circular import detection
- Class inheritance validation
"""

from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from difflib import get_close_matches

from ..parser.ast_nodes import *
from ..lexer.token import Position
from .types import (
    Type, PrimitiveType, ArrayType, MapType, FunctionType, ClassType,
    UnionType, TypeVariable, TypeUnifier, parse_type_annotation,
    TEXT_TYPE, DIGITS_TYPE, TF_TYPE, VOID_TYPE, GHOST_TYPE
)


# ============================================================================
# Symbol Table
# ============================================================================

@dataclass
class Symbol:
    """Represents a symbol in the symbol table."""
    name: str
    type: Type
    is_mutable: bool = True
    scope_level: int = 0
    position: Optional[Position] = None


class SymbolTable:
    """Manages symbols and scopes for semantic analysis."""
    
    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.symbols: Dict[str, Symbol] = {}
        self.parent = parent
        self.scope_level = 0 if parent is None else parent.scope_level + 1
    
    def define(self, name: str, symbol: Symbol) -> None:
        """Define a new symbol in the current scope."""
        self.symbols[name] = symbol
    
    def resolve(self, name: str) -> Optional[Symbol]:
        """Resolve a symbol, checking parent scopes if needed."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
        return None
    
    def resolve_local(self, name: str) -> Optional[Symbol]:
        """Resolve a symbol only in the current scope."""
        return self.symbols.get(name)
    
    def get_all_names(self) -> List[str]:
        """Get all symbol names in this scope and parent scopes."""
        names = list(self.symbols.keys())
        if self.parent:
            names.extend(self.parent.get_all_names())
        return names


# ============================================================================
# Semantic Errors
# ============================================================================

@dataclass
class SemanticError:
    """Represents a semantic error."""
    message: str
    position: Position
    suggestions: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        result = f"Semantic error at {self.position}: {self.message}"
        if self.suggestions:
            result += f"\n  Did you mean: {', '.join(self.suggestions)}?"
        return result



# ============================================================================
# Semantic Analyzer
# ============================================================================

class SemanticAnalyzer:
    """Performs semantic analysis on NoCapLang AST."""
    
    def __init__(self, ast: ProgramNode):
        self.ast = ast
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticError] = []
        self.current_function: Optional[FunctionDeclarationNode] = None
        self.loop_depth = 0
        self.imported_files: Set[str] = set()
        self.import_stack: List[str] = []
        self.classes: Dict[str, ClassType] = {}
        
        # Initialize built-in functions
        self._init_builtins()
    
    def _init_builtins(self) -> None:
        """Initialize built-in functions in the symbol table."""
        # String functions
        self.symbol_table.define("trim", Symbol("trim", FunctionType((TEXT_TYPE,), TEXT_TYPE, False), False, 0))
        self.symbol_table.define("uppercase", Symbol("uppercase", FunctionType((TEXT_TYPE,), TEXT_TYPE, False), False, 0))
        self.symbol_table.define("lowercase", Symbol("lowercase", FunctionType((TEXT_TYPE,), TEXT_TYPE, False), False, 0))
        self.symbol_table.define("length", Symbol("length", FunctionType((TEXT_TYPE,), DIGITS_TYPE, False), False, 0))
        self.symbol_table.define("len", Symbol("len", FunctionType((TEXT_TYPE,), DIGITS_TYPE, False), False, 0))
        
        # Math functions
        self.symbol_table.define("abs", Symbol("abs", FunctionType((DIGITS_TYPE,), DIGITS_TYPE, False), False, 0))
        self.symbol_table.define("sqrt", Symbol("sqrt", FunctionType((DIGITS_TYPE,), DIGITS_TYPE, False), False, 0))
        self.symbol_table.define("pow", Symbol("pow", FunctionType((DIGITS_TYPE, DIGITS_TYPE), DIGITS_TYPE, False), False, 0))
        self.symbol_table.define("round", Symbol("round", FunctionType((DIGITS_TYPE,), DIGITS_TYPE, False), False, 0))
        self.symbol_table.define("floor", Symbol("floor", FunctionType((DIGITS_TYPE,), DIGITS_TYPE, False), False, 0))
        self.symbol_table.define("ceil", Symbol("ceil", FunctionType((DIGITS_TYPE,), DIGITS_TYPE, False), False, 0))
        self.symbol_table.define("min", Symbol("min", FunctionType((DIGITS_TYPE, DIGITS_TYPE), DIGITS_TYPE, False), False, 0))
        self.symbol_table.define("max", Symbol("max", FunctionType((DIGITS_TYPE, DIGITS_TYPE), DIGITS_TYPE, False), False, 0))
        
        # Collection functions - use GHOST_TYPE for generic parameters to allow any type
        self.symbol_table.define("sort", Symbol("sort", FunctionType((GHOST_TYPE,), GHOST_TYPE, False), False, 0))
        self.symbol_table.define("reverse", Symbol("reverse", FunctionType((GHOST_TYPE,), GHOST_TYPE, False), False, 0))
        self.symbol_table.define("map", Symbol("map", FunctionType((GHOST_TYPE, GHOST_TYPE), GHOST_TYPE, False), False, 0))
        self.symbol_table.define("filter", Symbol("filter", FunctionType((GHOST_TYPE, GHOST_TYPE), GHOST_TYPE, False), False, 0))
        self.symbol_table.define("reduce", Symbol("reduce", FunctionType((GHOST_TYPE, GHOST_TYPE, GHOST_TYPE), GHOST_TYPE, False), False, 0))
        self.symbol_table.define("has", Symbol("has", FunctionType((GHOST_TYPE, GHOST_TYPE), TF_TYPE, False), False, 0))
    
    def analyze(self) -> Tuple[ProgramNode, List[SemanticError]]:
        """Perform semantic analysis on the AST.
        
        Returns:
            Tuple of (annotated AST, list of errors)
        """
        # First pass: collect all class and function declarations
        self._collect_declarations(self.ast)
        
        # Second pass: analyze all statements
        for statement in self.ast.statements:
            self._analyze_statement(statement)
        
        return self.ast, self.errors
    
    def _collect_declarations(self, program: ProgramNode) -> None:
        """First pass: collect all top-level declarations."""
        for statement in program.statements:
            if isinstance(statement, ClassDeclarationNode):
                self._collect_class(statement)
            elif isinstance(statement, FunctionDeclarationNode):
                self._collect_function(statement)
    
    def _collect_class(self, node: ClassDeclarationNode) -> None:
        """Collect a class declaration."""
        # Check for duplicate class names
        if node.name in self.classes:
            self.errors.append(SemanticError(
                f"Class '{node.name}' is already defined",
                node.position
            ))
            return
        
        # Create class type
        class_type = ClassType(node.name, {}, {}, None)
        self.classes[node.name] = class_type
        
        # Define class in symbol table
        self.symbol_table.define(node.name, Symbol(
            node.name, class_type, False, self.symbol_table.scope_level, node.position
        ))
    
    def _collect_function(self, node: FunctionDeclarationNode) -> None:
        """Collect a function declaration."""
        # Parse parameter types
        param_types = []
        for param_name, type_annotation in node.parameters:
            if type_annotation:
                param_types.append(parse_type_annotation(type_annotation))
            else:
                param_types.append(TypeVariable(f"T_{param_name}"))
        
        # Parse return type
        return_type = VOID_TYPE
        if node.return_type:
            return_type = parse_type_annotation(node.return_type)
        
        # Create function type
        func_type = FunctionType(tuple(param_types), return_type, node.is_async)
        
        # Define function in symbol table
        self.symbol_table.define(node.name, Symbol(
            node.name, func_type, False, self.symbol_table.scope_level, node.position
        ))
    
    def _analyze_statement(self, node: StatementNode) -> None:
        """Analyze a statement node."""
        if isinstance(node, VariableDeclarationNode):
            self._analyze_variable_declaration(node)
        elif isinstance(node, FunctionDeclarationNode):
            self._analyze_function_declaration(node)
        elif isinstance(node, ClassDeclarationNode):
            self._analyze_class_declaration(node)
        elif isinstance(node, AssignmentNode):
            self._analyze_assignment(node)
        elif isinstance(node, ExpressionStatementNode):
            self._analyze_expression(node.expression)
        elif isinstance(node, PrintStatementNode):
            self._analyze_print_statement(node)
        elif isinstance(node, IfStatementNode):
            self._analyze_if_statement(node)
        elif isinstance(node, ForLoopNode):
            self._analyze_for_loop(node)
        elif isinstance(node, WhileLoopNode):
            self._analyze_while_loop(node)
        elif isinstance(node, ForEachLoopNode):
            self._analyze_foreach_loop(node)
        elif isinstance(node, ReturnStatementNode):
            self._analyze_return_statement(node)
        elif isinstance(node, BreakStatementNode):
            self._analyze_break_statement(node)
        elif isinstance(node, ContinueStatementNode):
            self._analyze_continue_statement(node)
        elif isinstance(node, TryStatementNode):
            self._analyze_try_statement(node)
        elif isinstance(node, ThrowStatementNode):
            self._analyze_throw_statement(node)
        elif isinstance(node, AssertStatementNode):
            self._analyze_assert_statement(node)
        elif isinstance(node, MatchStatementNode):
            self._analyze_match_statement(node)
        elif isinstance(node, ImportNode):
            self._analyze_import(node)
    
    def _analyze_variable_declaration(self, node: VariableDeclarationNode) -> None:
        """Analyze a variable declaration."""
        # Check if variable already exists in current scope
        existing = self.symbol_table.resolve_local(node.name)
        if existing:
            # Allow shadowing of built-in functions (they are immutable and at scope 0)
            is_builtin = existing.scope_level == 0 and not existing.is_mutable
            if not is_builtin:
                self.errors.append(SemanticError(
                    f"Variable '{node.name}' is already defined in this scope",
                    node.position
                ))
                return
        
        # Determine variable type
        var_type = GHOST_TYPE
        if node.initializer:
            var_type = self._analyze_expression(node.initializer)
        
        # If type annotation is provided, check compatibility
        if node.type_annotation:
            annotated_type = parse_type_annotation(node.type_annotation)
            
            # If it's a TypeVariable, try to resolve it as a class name
            if isinstance(annotated_type, TypeVariable):
                class_symbol = self.symbol_table.resolve(annotated_type.name)
                if class_symbol and isinstance(class_symbol.type, ClassType):
                    annotated_type = class_symbol.type
            
            if node.initializer and not var_type.is_compatible_with(annotated_type):
                self.errors.append(SemanticError(
                    f"Type mismatch: cannot assign {var_type} to {annotated_type}",
                    node.position
                ))
            var_type = annotated_type
        
        # Define variable in symbol table
        self.symbol_table.define(node.name, Symbol(
            node.name, var_type, True, self.symbol_table.scope_level, node.position
        ))
    
    def _analyze_function_declaration(self, node: FunctionDeclarationNode) -> None:
        """Analyze a function declaration."""
        # Save current function context
        prev_function = self.current_function
        self.current_function = node
        
        # Create new scope for function
        prev_table = self.symbol_table
        self.symbol_table = SymbolTable(prev_table)
        
        # Add parameters to scope
        for param_name, type_annotation in node.parameters:
            param_type = GHOST_TYPE
            if type_annotation:
                param_type = parse_type_annotation(type_annotation)
            self.symbol_table.define(param_name, Symbol(
                param_name, param_type, True, self.symbol_table.scope_level, node.position
            ))
        
        # Analyze function body
        for statement in node.body:
            self._analyze_statement(statement)
        
        # Restore previous context
        self.symbol_table = prev_table
        self.current_function = prev_function
    
    def _analyze_class_declaration(self, node: ClassDeclarationNode) -> None:
        """Analyze a class declaration."""
        class_type = self.classes.get(node.name)
        if not class_type:
            return  # Error already reported in collection phase
        
        # Resolve parent class if specified
        if node.parent:
            parent_symbol = self.symbol_table.resolve(node.parent)
            if not parent_symbol:
                self.errors.append(SemanticError(
                    f"Parent class '{node.parent}' is not defined",
                    node.position
                ))
            elif not isinstance(parent_symbol.type, ClassType):
                self.errors.append(SemanticError(
                    f"'{node.parent}' is not a class",
                    node.position
                ))
            else:
                class_type.parent = parent_symbol.type
                
                # Check for circular inheritance
                if class_type.has_circular_inheritance():
                    self.errors.append(SemanticError(
                        f"Circular inheritance detected for class '{node.name}'",
                        node.position
                    ))
        
        # Create new scope for class
        prev_table = self.symbol_table
        self.symbol_table = SymbolTable(prev_table)
        
        # Add 'self' to scope
        self.symbol_table.define("self", Symbol(
            "self", class_type, False, self.symbol_table.scope_level, node.position
        ))
        
        # Analyze fields
        for field in node.fields:
            self._analyze_variable_declaration(field)
            if field.name in class_type.fields:
                self.errors.append(SemanticError(
                    f"Field '{field.name}' is already defined in class '{node.name}'",
                    field.position
                ))
            else:
                field_symbol = self.symbol_table.resolve_local(field.name)
                if field_symbol:
                    class_type.fields[field.name] = field_symbol.type
        
        # Analyze methods
        for method in node.methods:
            # Parse method signature to get function type
            param_types = []
            for param_name, type_annotation in method.parameters:
                if type_annotation:
                    param_types.append(parse_type_annotation(type_annotation))
                else:
                    param_types.append(TypeVariable(f"T_{param_name}"))
            
            return_type = VOID_TYPE
            if method.return_type:
                return_type = parse_type_annotation(method.return_type)
            
            method_type = FunctionType(tuple(param_types), return_type, method.is_async)
            class_type.methods[method.name] = method_type
            
            # Now analyze the method body
            self._analyze_function_declaration(method)
        
        # Restore previous scope
        self.symbol_table = prev_table
    
    def _analyze_assignment(self, node: AssignmentNode) -> None:
        """Analyze an assignment statement."""
        # Analyze the value being assigned
        value_type = self._analyze_expression(node.value)
        
        # Analyze the target
        if isinstance(node.target, IdentifierNode):
            # Simple variable assignment
            symbol = self.symbol_table.resolve(node.target.name)
            if not symbol:
                # Suggest similar names
                suggestions = get_close_matches(
                    node.target.name, 
                    self.symbol_table.get_all_names(),
                    n=3, cutoff=0.6
                )
                self.errors.append(SemanticError(
                    f"Undefined variable '{node.target.name}'",
                    node.target.position,
                    suggestions
                ))
            elif not symbol.is_mutable:
                self.errors.append(SemanticError(
                    f"Cannot assign to immutable variable '{node.target.name}'",
                    node.target.position
                ))
            elif not value_type.is_compatible_with(symbol.type):
                self.errors.append(SemanticError(
                    f"Type mismatch: cannot assign {value_type} to {symbol.type}",
                    node.position
                ))
        else:
            # Index or member access assignment
            target_type = self._analyze_expression(node.target)
            # Type checking for complex assignments would go here
    
    def _analyze_print_statement(self, node: PrintStatementNode) -> None:
        """Analyze a print statement."""
        for arg in node.arguments:
            self._analyze_expression(arg)
    
    def _analyze_if_statement(self, node: IfStatementNode) -> None:
        """Analyze an if statement."""
        # Analyze condition
        cond_type = self._analyze_expression(node.condition)
        if not cond_type.is_compatible_with(TF_TYPE):
            self.errors.append(SemanticError(
                f"Condition must be of type tf, got {cond_type}",
                node.condition.position
            ))
        
        # Analyze then branch
        self._enter_scope()
        for statement in node.then_branch:
            self._analyze_statement(statement)
        self._exit_scope()
        
        # Analyze elif branches
        for elif_cond, elif_body in node.elif_branches:
            elif_type = self._analyze_expression(elif_cond)
            if not elif_type.is_compatible_with(TF_TYPE):
                self.errors.append(SemanticError(
                    f"Condition must be of type tf, got {elif_type}",
                    elif_cond.position
                ))
            self._enter_scope()
            for statement in elif_body:
                self._analyze_statement(statement)
            self._exit_scope()
        
        # Analyze else branch
        if node.else_branch:
            self._enter_scope()
            for statement in node.else_branch:
                self._analyze_statement(statement)
            self._exit_scope()
    
    def _analyze_for_loop(self, node: ForLoopNode) -> None:
        """Analyze a for loop."""
        self._enter_scope()
        self.loop_depth += 1
        
        if node.initializer:
            self._analyze_statement(node.initializer)
        if node.condition:
            cond_type = self._analyze_expression(node.condition)
            if not cond_type.is_compatible_with(TF_TYPE):
                self.errors.append(SemanticError(
                    f"Loop condition must be of type tf, got {cond_type}",
                    node.condition.position
                ))
        if node.increment:
            self._analyze_expression(node.increment)
        
        for statement in node.body:
            self._analyze_statement(statement)
        
        self.loop_depth -= 1
        self._exit_scope()
    
    def _analyze_while_loop(self, node: WhileLoopNode) -> None:
        """Analyze a while loop."""
        cond_type = self._analyze_expression(node.condition)
        if not cond_type.is_compatible_with(TF_TYPE):
            self.errors.append(SemanticError(
                f"Loop condition must be of type tf, got {cond_type}",
                node.condition.position
            ))
        
        self._enter_scope()
        self.loop_depth += 1
        
        for statement in node.body:
            self._analyze_statement(statement)
        
        self.loop_depth -= 1
        self._exit_scope()
    
    def _analyze_foreach_loop(self, node: ForEachLoopNode) -> None:
        """Analyze a for-each loop."""
        # Analyze iterable
        iterable_type = self._analyze_expression(node.iterable)
        
        self._enter_scope()
        self.loop_depth += 1
        
        # Determine element type and define loop variable
        if isinstance(iterable_type, ArrayType):
            self.symbol_table.define(node.variable, Symbol(
                node.variable, iterable_type.element_type, True,
                self.symbol_table.scope_level, node.position
            ))
        elif isinstance(iterable_type, MapType):
            # For bags, define both key and value variables
            if node.key_variable:
                self.symbol_table.define(node.key_variable, Symbol(
                    node.key_variable, iterable_type.key_type, True,
                    self.symbol_table.scope_level, node.position
                ))
            self.symbol_table.define(node.variable, Symbol(
                node.variable, iterable_type.value_type, True,
                self.symbol_table.scope_level, node.position
            ))
        else:
            self.errors.append(SemanticError(
                f"Cannot iterate over type {iterable_type}",
                node.iterable.position
            ))
        
        for statement in node.body:
            self._analyze_statement(statement)
        
        self.loop_depth -= 1
        self._exit_scope()
    
    def _analyze_return_statement(self, node: ReturnStatementNode) -> None:
        """Analyze a return statement."""
        if not self.current_function:
            self.errors.append(SemanticError(
                "Return statement outside of function",
                node.position
            ))
            return
        
        if node.value:
            return_type = self._analyze_expression(node.value)
            # Check if return type matches function signature
            # (This would require tracking expected return type)
    
    def _analyze_break_statement(self, node: BreakStatementNode) -> None:
        """Analyze a break statement."""
        if self.loop_depth == 0:
            self.errors.append(SemanticError(
                "Break statement outside of loop",
                node.position
            ))
    
    def _analyze_continue_statement(self, node: ContinueStatementNode) -> None:
        """Analyze a continue statement."""
        if self.loop_depth == 0:
            self.errors.append(SemanticError(
                "Continue statement outside of loop",
                node.position
            ))
    
    def _analyze_try_statement(self, node: TryStatementNode) -> None:
        """Analyze a try-catch-finally statement."""
        # Analyze try block
        self._enter_scope()
        for statement in node.try_block:
            self._analyze_statement(statement)
        self._exit_scope()
        
        # Analyze catch block
        if node.catch_block:
            self._enter_scope()
            if node.catch_variable:
                # Define error variable
                self.symbol_table.define(node.catch_variable, Symbol(
                    node.catch_variable, TEXT_TYPE, True,
                    self.symbol_table.scope_level, node.position
                ))
            for statement in node.catch_block:
                self._analyze_statement(statement)
            self._exit_scope()
        
        # Analyze finally block
        if node.finally_block:
            self._enter_scope()
            for statement in node.finally_block:
                self._analyze_statement(statement)
            self._exit_scope()
    
    def _analyze_throw_statement(self, node: ThrowStatementNode) -> None:
        """Analyze a throw statement."""
        self._analyze_expression(node.expression)
    
    def _analyze_assert_statement(self, node: AssertStatementNode) -> None:
        """Analyze an assert statement."""
        cond_type = self._analyze_expression(node.condition)
        if not cond_type.is_compatible_with(TF_TYPE):
            self.errors.append(SemanticError(
                f"Assertion condition must be of type tf, got {cond_type}",
                node.condition.position
            ))
        if node.message:
            self._analyze_expression(node.message)
    
    def _analyze_match_statement(self, node: MatchStatementNode) -> None:
        """Analyze a match statement."""
        # Analyze the expression being matched
        match_type = self._analyze_expression(node.expression)
        
        # Analyze each case
        for case in node.cases:
            self._enter_scope()
            self._analyze_expression(case.pattern)
            if case.guard:
                guard_type = self._analyze_expression(case.guard)
                if not guard_type.is_compatible_with(TF_TYPE):
                    self.errors.append(SemanticError(
                        f"Case guard must be of type tf, got {guard_type}",
                        case.guard.position
                    ))
            for statement in case.body:
                self._analyze_statement(statement)
            self._exit_scope()
        
        # Analyze default case
        if node.default_case:
            self._enter_scope()
            for statement in node.default_case:
                self._analyze_statement(statement)
            self._exit_scope()
    
    def _analyze_import(self, node: ImportNode) -> None:
        """Analyze an import statement."""
        # Check for circular imports
        if node.path in self.import_stack:
            self.errors.append(SemanticError(
                f"Circular import detected: {' -> '.join(self.import_stack + [node.path])}",
                node.position
            ))
            return
        
        # Mark file as imported
        self.imported_files.add(node.path)
        
        # In a real implementation, we would:
        # 1. Load and parse the imported file
        # 2. Analyze it with import_stack updated
        # 3. Import the specified symbols into current scope
    
    def _analyze_expression(self, node: ExpressionNode) -> Type:
        """Analyze an expression and return its type."""
        if isinstance(node, LiteralNode):
            return self._analyze_literal(node)
        elif isinstance(node, IdentifierNode):
            return self._analyze_identifier(node)
        elif isinstance(node, BinaryOpNode):
            return self._analyze_binary_op(node)
        elif isinstance(node, UnaryOpNode):
            return self._analyze_unary_op(node)
        elif isinstance(node, CallNode):
            return self._analyze_call(node)
        elif isinstance(node, IndexNode):
            return self._analyze_index(node)
        elif isinstance(node, MemberAccessNode):
            return self._analyze_member_access(node)
        elif isinstance(node, ArrayLiteralNode):
            return self._analyze_array_literal(node)
        elif isinstance(node, ObjectLiteralNode):
            return self._analyze_object_literal(node)
        elif isinstance(node, AwaitNode):
            return self._analyze_await(node)
        elif isinstance(node, NewNode):
            return self._analyze_new(node)
        elif isinstance(node, LambdaNode):
            return self._analyze_lambda(node)
        else:
            return GHOST_TYPE
    
    def _analyze_literal(self, node: LiteralNode) -> Type:
        """Analyze a literal expression."""
        if node.value is None:
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
        elif isinstance(node.value, bool):
            node.expr_type = TF_TYPE
            return TF_TYPE
        elif isinstance(node.value, (int, float)):
            node.expr_type = DIGITS_TYPE
            return DIGITS_TYPE
        elif isinstance(node.value, str):
            node.expr_type = TEXT_TYPE
            return TEXT_TYPE
        else:
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
    
    def _analyze_identifier(self, node: IdentifierNode) -> Type:
        """Analyze an identifier expression."""
        symbol = self.symbol_table.resolve(node.name)
        if not symbol:
            # Suggest similar names
            suggestions = get_close_matches(
                node.name,
                self.symbol_table.get_all_names(),
                n=3, cutoff=0.6
            )
            self.errors.append(SemanticError(
                f"Undefined variable '{node.name}'",
                node.position,
                suggestions
            ))
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
        
        node.expr_type = symbol.type
        return symbol.type
    
    def _analyze_binary_op(self, node: BinaryOpNode) -> Type:
        """Analyze a binary operation."""
        left_type = self._analyze_expression(node.left)
        right_type = self._analyze_expression(node.right)
        
        # Special handling for + operator (supports both arithmetic and string concatenation)
        if node.operator == '+':
            # If either operand is text, treat as string concatenation
            if left_type.is_compatible_with(TEXT_TYPE) or right_type.is_compatible_with(TEXT_TYPE):
                node.expr_type = TEXT_TYPE
                return TEXT_TYPE
            # Otherwise, treat as arithmetic addition
            elif left_type.is_compatible_with(DIGITS_TYPE) and right_type.is_compatible_with(DIGITS_TYPE):
                node.expr_type = DIGITS_TYPE
                return DIGITS_TYPE
            else:
                self.errors.append(SemanticError(
                    f"Operator '+' requires either text or digits operands, got {left_type} and {right_type}",
                    node.position
                ))
                node.expr_type = GHOST_TYPE
                return GHOST_TYPE
        
        # Other arithmetic operators (only for digits)
        elif node.operator in ['-', '*', '/', '%']:
            if not left_type.is_compatible_with(DIGITS_TYPE):
                self.errors.append(SemanticError(
                    f"Left operand of '{node.operator}' must be digits, got {left_type}",
                    node.left.position
                ))
            if not right_type.is_compatible_with(DIGITS_TYPE):
                self.errors.append(SemanticError(
                    f"Right operand of '{node.operator}' must be digits, got {right_type}",
                    node.right.position
                ))
            node.expr_type = DIGITS_TYPE
            return DIGITS_TYPE
        
        # Comparison operators
        elif node.operator in ['==', '!=', '<', '>', '<=', '>=']:
            # Allow comparison of compatible types
            if not left_type.is_compatible_with(right_type) and not right_type.is_compatible_with(left_type):
                self.errors.append(SemanticError(
                    f"Cannot compare {left_type} with {right_type}",
                    node.position
                ))
            node.expr_type = TF_TYPE
            return TF_TYPE
        
        # Logical operators
        elif node.operator in ['and', 'or']:
            if not left_type.is_compatible_with(TF_TYPE):
                self.errors.append(SemanticError(
                    f"Left operand of '{node.operator}' must be tf, got {left_type}",
                    node.left.position
                ))
            if not right_type.is_compatible_with(TF_TYPE):
                self.errors.append(SemanticError(
                    f"Right operand of '{node.operator}' must be tf, got {right_type}",
                    node.right.position
                ))
            node.expr_type = TF_TYPE
            return TF_TYPE
        
        else:
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
    
    def _analyze_unary_op(self, node: UnaryOpNode) -> Type:
        """Analyze a unary operation."""
        operand_type = self._analyze_expression(node.operand)
        
        if node.operator == '-':
            if not operand_type.is_compatible_with(DIGITS_TYPE):
                self.errors.append(SemanticError(
                    f"Operand of unary '-' must be digits, got {operand_type}",
                    node.operand.position
                ))
            node.expr_type = DIGITS_TYPE
            return DIGITS_TYPE
        
        elif node.operator == 'not':
            if not operand_type.is_compatible_with(TF_TYPE):
                self.errors.append(SemanticError(
                    f"Operand of 'not' must be tf, got {operand_type}",
                    node.operand.position
                ))
            node.expr_type = TF_TYPE
            return TF_TYPE
        
        else:
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
    
    def _analyze_call(self, node: CallNode) -> Type:
        """Analyze a function call."""
        callee_type = self._analyze_expression(node.callee)
        
        # Analyze arguments
        arg_types = [self._analyze_expression(arg) for arg in node.arguments]
        
        # Check if callee is a class (class instantiation)
        if isinstance(callee_type, ClassType):
            # This is class instantiation - check if init method exists
            init_method = callee_type.get_method("init")
            if init_method and isinstance(init_method, FunctionType):
                # Check argument count and types against init method
                if len(arg_types) != len(init_method.param_types):
                    self.errors.append(SemanticError(
                        f"Constructor expects {len(init_method.param_types)} arguments, got {len(arg_types)}",
                        node.position
                    ))
                else:
                    # Check argument types
                    for i, (arg_type, param_type) in enumerate(zip(arg_types, init_method.param_types)):
                        if not arg_type.is_compatible_with(param_type) and not param_type.is_compatible_with(arg_type):
                            self.errors.append(SemanticError(
                                f"Argument {i+1} type mismatch: expected {param_type}, got {arg_type}",
                                node.arguments[i].position
                            ))
            
            # Return the class type (instance of the class)
            node.expr_type = callee_type
            return callee_type
        
        # Check if callee is a function
        elif isinstance(callee_type, FunctionType):
            # Check argument count
            if len(arg_types) != len(callee_type.param_types):
                self.errors.append(SemanticError(
                    f"Function expects {len(callee_type.param_types)} arguments, got {len(arg_types)}",
                    node.position
                ))
            else:
                # Check argument types
                for i, (arg_type, param_type) in enumerate(zip(arg_types, callee_type.param_types)):
                    # Allow if either direction is compatible (handles ghost type)
                    if not arg_type.is_compatible_with(param_type) and not param_type.is_compatible_with(arg_type):
                        self.errors.append(SemanticError(
                            f"Argument {i+1} type mismatch: expected {param_type}, got {arg_type}",
                            node.arguments[i].position
                        ))
            
            node.expr_type = callee_type.return_type
            return callee_type.return_type
        
        else:
            self.errors.append(SemanticError(
                f"Cannot call non-function type {callee_type}",
                node.callee.position
            ))
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
    
    def _analyze_index(self, node: IndexNode) -> Type:
        """Analyze an index operation."""
        object_type = self._analyze_expression(node.object)
        index_type = self._analyze_expression(node.index)
        
        if isinstance(object_type, ArrayType):
            # Check index is digits
            if not index_type.is_compatible_with(DIGITS_TYPE):
                self.errors.append(SemanticError(
                    f"Array index must be digits, got {index_type}",
                    node.index.position
                ))
            node.expr_type = object_type.element_type
            return object_type.element_type
        
        elif isinstance(object_type, MapType):
            # Check index is compatible with key type
            if not index_type.is_compatible_with(object_type.key_type):
                self.errors.append(SemanticError(
                    f"Map key must be {object_type.key_type}, got {index_type}",
                    node.index.position
                ))
            node.expr_type = object_type.value_type
            return object_type.value_type
        
        else:
            self.errors.append(SemanticError(
                f"Cannot index type {object_type}",
                node.object.position
            ))
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
    
    def _analyze_member_access(self, node: MemberAccessNode) -> Type:
        """Analyze a member access operation."""
        object_type = self._analyze_expression(node.object)
        
        if isinstance(object_type, ClassType):
            # Check if field exists
            field_type = object_type.get_field(node.member)
            if field_type:
                node.expr_type = field_type
                return field_type
            
            # Check if method exists
            method_type = object_type.get_method(node.member)
            if method_type:
                node.expr_type = method_type
                return method_type
            
            self.errors.append(SemanticError(
                f"Class '{object_type.name}' has no member '{node.member}'",
                node.position
            ))
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
        
        else:
            self.errors.append(SemanticError(
                f"Cannot access member of non-class type {object_type}",
                node.object.position
            ))
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
    
    def _analyze_array_literal(self, node: ArrayLiteralNode) -> Type:
        """Analyze an array literal."""
        if not node.elements:
            # Empty array - type is lineup<ghost>
            node.expr_type = ArrayType(GHOST_TYPE)
            return node.expr_type
        
        # Infer element type from first element
        element_types = [self._analyze_expression(elem) for elem in node.elements]
        element_type = element_types[0]
        
        # Check all elements have compatible types
        for i, elem_type in enumerate(element_types[1:], 1):
            if not elem_type.is_compatible_with(element_type):
                self.errors.append(SemanticError(
                    f"Array element {i} has incompatible type: expected {element_type}, got {elem_type}",
                    node.elements[i].position
                ))
        
        node.expr_type = ArrayType(element_type)
        return node.expr_type
    
    def _analyze_object_literal(self, node: ObjectLiteralNode) -> Type:
        """Analyze an object literal."""
        if not node.pairs:
            # Empty object - type is bag<ghost, ghost>
            node.expr_type = MapType(GHOST_TYPE, GHOST_TYPE)
            return node.expr_type
        
        # Infer key and value types from first pair
        key_types = []
        value_types = []
        for key_expr, value_expr in node.pairs:
            key_types.append(self._analyze_expression(key_expr))
            value_types.append(self._analyze_expression(value_expr))
        
        key_type = key_types[0]
        
        # Check if all values have the same type
        all_same_value_type = all(v_type.is_compatible_with(value_types[0]) for v_type in value_types)
        
        if all_same_value_type:
            # Homogeneous object - use specific value type
            value_type = value_types[0]
        else:
            # Heterogeneous object - use ghost type for values
            value_type = GHOST_TYPE
        
        # Check all keys have compatible types (keys should be homogeneous)
        for i, k_type in enumerate(key_types[1:], 1):
            if not k_type.is_compatible_with(key_type):
                self.errors.append(SemanticError(
                    f"Object key {i} has incompatible type: expected {key_type}, got {k_type}",
                    node.pairs[i][0].position
                ))
        
        node.expr_type = MapType(key_type, value_type)
        return node.expr_type
    
    def _analyze_await(self, node: AwaitNode) -> Type:
        """Analyze an await expression."""
        # Check if we're in an async function
        if not self.current_function or not self.current_function.is_async:
            self.errors.append(SemanticError(
                "Await expression outside of async function",
                node.position
            ))
        
        expr_type = self._analyze_expression(node.expression)
        node.expr_type = expr_type
        return expr_type
    
    def _analyze_new(self, node: NewNode) -> Type:
        """Analyze a class instantiation."""
        # Resolve class name
        symbol = self.symbol_table.resolve(node.class_name)
        if not symbol:
            self.errors.append(SemanticError(
                f"Undefined class '{node.class_name}'",
                node.position
            ))
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
        
        if not isinstance(symbol.type, ClassType):
            self.errors.append(SemanticError(
                f"'{node.class_name}' is not a class",
                node.position
            ))
            node.expr_type = GHOST_TYPE
            return GHOST_TYPE
        
        # Analyze constructor arguments
        for arg in node.arguments:
            self._analyze_expression(arg)
        
        node.expr_type = symbol.type
        return symbol.type
    
    def _analyze_lambda(self, node: LambdaNode) -> Type:
        """Analyze a lambda expression."""
        # Parse parameter types
        param_types = []
        for param_name, type_annotation in node.parameters:
            if type_annotation:
                param_types.append(parse_type_annotation(type_annotation))
            else:
                param_types.append(TypeVariable(f"T_{param_name}"))
        
        # Parse return type
        return_type = VOID_TYPE
        if node.return_type:
            return_type = parse_type_annotation(node.return_type)
        
        # Create new scope for lambda
        prev_table = self.symbol_table
        self.symbol_table = SymbolTable(prev_table)
        
        # Add parameters to scope
        for (param_name, _), param_type in zip(node.parameters, param_types):
            self.symbol_table.define(param_name, Symbol(
                param_name, param_type, True, self.symbol_table.scope_level, node.position
            ))
        
        # Analyze lambda body
        for statement in node.body:
            self._analyze_statement(statement)
        
        # Restore previous scope
        self.symbol_table = prev_table
        
        func_type = FunctionType(tuple(param_types), return_type, False)
        node.expr_type = func_type
        return func_type
    
    def _enter_scope(self) -> None:
        """Enter a new scope."""
        self.symbol_table = SymbolTable(self.symbol_table)
    
    def _exit_scope(self) -> None:
        """Exit the current scope."""
        if self.symbol_table.parent:
            self.symbol_table = self.symbol_table.parent
