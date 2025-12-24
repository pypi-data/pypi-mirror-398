"""Parser for NoCapLang.

This module implements a recursive descent parser with operator precedence climbing
for expressions. It consumes tokens from the lexer and builds an Abstract Syntax Tree (AST).
"""

from typing import List, Optional, Union
from ..lexer.lexer import Lexer
from ..lexer.token import Token, TokenType, Position
from .ast_nodes import *


class ParseError(Exception):
    """Exception raised during parsing."""
    
    def __init__(self, message: str, position: Position):
        self.message = message
        self.position = position
        super().__init__(f"{position}: {message}")


class Parser:
    """Recursive descent parser for NoCapLang."""
    
    def __init__(self, lexer: Lexer):
        """Initialize parser with a lexer.
        
        Args:
            lexer: The lexer to consume tokens from
        """
        self.lexer = lexer
        self.tokens = lexer.scan_tokens()
        self.token_index = 0
        self.current_token = None
        self.previous_token = None
        self.errors = []
        self.panic_mode = False
        
        # Advance to first token
        self.advance()
    
    # ========================================================================
    # Token Management
    # ========================================================================
    
    def advance(self) -> Token:
        """Consume the current token and move to the next."""
        self.previous_token = self.current_token
        
        # Skip newlines in most contexts (they're only significant as statement separators)
        while True:
            if self.token_index < len(self.tokens):
                self.current_token = self.tokens[self.token_index]
                self.token_index += 1
            else:
                # Stay at EOF
                self.current_token = self.tokens[-1] if self.tokens else None
            
            if self.current_token.type != TokenType.NEWLINE:
                break
        
        return self.previous_token
    
    def check(self, token_type: TokenType) -> bool:
        """Check if current token matches the given type."""
        return self.current_token.type == token_type
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False
    
    def consume(self, token_type: TokenType, message: str) -> Token:
        """Consume a token of the given type or raise an error."""
        if self.check(token_type):
            return self.advance()
        
        self.error(message)
        raise ParseError(message, self.current_token.position)
    
    def error(self, message: str):
        """Report a parse error."""
        if self.panic_mode:
            return
        
        self.panic_mode = True
        error = ParseError(message, self.current_token.position)
        self.errors.append(error)
    
    def synchronize(self):
        """Synchronize after an error by skipping to the next statement boundary."""
        self.panic_mode = False
        
        while not self.check(TokenType.EOF):
            # Statement boundaries
            if self.previous_token.type == TokenType.NEWLINE:
                return
            
            # Keywords that start statements
            if self.current_token.type in [
                TokenType.FR, TokenType.LOWKEY, TokenType.VIBE,
                TokenType.VIBECHECK, TokenType.RUN, TokenType.UNTIL,
                TokenType.EACH, TokenType.COMEBACK, TokenType.TRYNA,
                TokenType.MATCH, TokenType.GRAB, TokenType.YAP
            ]:
                return
            
            self.advance()
    
    # ========================================================================
    # Main Parsing Entry Point
    # ========================================================================
    
    def parse_program(self) -> ProgramNode:
        """Parse a complete program.
        
        Returns:
            ProgramNode containing all statements
        """
        position = self.current_token.position
        statements = []
        
        while not self.check(TokenType.EOF):
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParseError:
                self.synchronize()
        
        return ProgramNode(position, statements)
    
    # ========================================================================
    # Statement Parsing
    # ========================================================================
    
    def parse_statement(self) -> Optional[StatementNode]:
        """Parse a single statement."""
        # Skip empty lines
        if self.check(TokenType.NEWLINE):
            self.advance()
            return None
        
        # Import statement
        if self.match(TokenType.GRAB):
            return self.parse_import()
        
        # Variable declaration
        if self.match(TokenType.FR):
            return self.parse_variable_declaration()
        
        # Function declaration
        if self.check(TokenType.LOWKEY) or self.check(TokenType.CHILL):
            return self.parse_function_declaration()
        
        # Class declaration
        if self.match(TokenType.VIBE):
            return self.parse_class_declaration()
        
        # Enum declaration
        if self.match(TokenType.CHOICES):
            return self.parse_enum_declaration()
        
        # Print statement
        if self.match(TokenType.YAP):
            return self.parse_print_statement()
        
        # If statement
        if self.match(TokenType.VIBECHECK):
            return self.parse_if_statement()
        
        # For loop
        if self.match(TokenType.RUN):
            return self.parse_for_loop()
        
        # While loop
        if self.match(TokenType.UNTIL):
            return self.parse_while_loop()
        
        # For-each loop
        if self.match(TokenType.EACH):
            return self.parse_foreach_loop()
        
        # Return statement
        if self.match(TokenType.COMEBACK):
            return self.parse_return_statement()
        
        # Break statement
        if self.match(TokenType.DIP):
            return self.parse_break_statement()
        
        # Continue statement
        if self.match(TokenType.SKIP):
            return self.parse_continue_statement()
        
        # Try-catch statement
        if self.match(TokenType.TRYNA):
            return self.parse_try_statement()
        
        # Throw statement
        if self.match(TokenType.CRASH):
            return self.parse_throw_statement()
        
        # Assert statement
        if self.match(TokenType.NOCAP):
            return self.parse_assert_statement()
        
        # Match statement (check/match)
        if self.match(TokenType.CHECK, TokenType.MATCH):
            return self.parse_match_statement()
        
        # Expression statement or assignment
        return self.parse_expression_statement()

    
    def parse_import(self) -> ImportNode:
        """Parse a 'grab' import statement.
        
        Grammar: grab "path" | grab { symbol1, symbol2 } from "path"
        """
        position = self.previous_token.position
        
        # Check for selective import: grab { symbols } from "path"
        if self.match(TokenType.LEFT_BRACE):
            symbols = []
            symbols.append(self.consume(TokenType.IDENTIFIER, "Expected symbol name").lexeme)
            
            while self.match(TokenType.COMMA):
                symbols.append(self.consume(TokenType.IDENTIFIER, "Expected symbol name").lexeme)
            
            self.consume(TokenType.RIGHT_BRACE, "Expected '}' after symbols")
            self.consume(TokenType.IDENTIFIER, "Expected 'from' keyword")  # 'from'
            path = self.consume(TokenType.STRING, "Expected import path").literal
            
            return ImportNode(position, path, symbols)
        
        # Simple import: grab "path"
        path = self.consume(TokenType.STRING, "Expected import path").literal
        return ImportNode(position, path, None)
    
    def parse_variable_declaration(self) -> VariableDeclarationNode:
        """Parse a 'fr' variable declaration.
        
        Grammar: fr name [: type] [= expression]
        """
        position = self.previous_token.position
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name").lexeme
        
        # Optional type annotation
        type_annotation = None
        if self.match(TokenType.COLON):
            type_annotation = self.parse_type_annotation()
        
        # Optional initializer
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.parse_expression()
        
        return VariableDeclarationNode(position, name, type_annotation, initializer)
    
    def parse_function_declaration(self) -> FunctionDeclarationNode:
        """Parse a 'lowkey' or 'chill lowkey' function declaration.
        
        Grammar: [chill] lowkey name(params) [: return_type] { body }
        """
        is_async = self.match(TokenType.CHILL)
        position = self.current_token.position
        self.consume(TokenType.LOWKEY, "Expected 'lowkey' keyword")
        
        name = self.consume(TokenType.IDENTIFIER, "Expected function name").lexeme
        
        # Parameters
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after function name")
        parameters = []
        
        if not self.check(TokenType.RIGHT_PAREN):
            parameters.append(self.parse_parameter())
            while self.match(TokenType.COMMA):
                parameters.append(self.parse_parameter())
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters")
        
        # Optional return type
        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.parse_type_annotation()
        
        # Body
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before function body")
        body = self.parse_block()
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after function body")
        
        return FunctionDeclarationNode(position, name, parameters, body, return_type, is_async)
    
    def parse_parameter(self) -> tuple[str, Optional[str]]:
        """Parse a function parameter.
        
        Grammar: name [: type]
        """
        name = self.consume(TokenType.IDENTIFIER, "Expected parameter name").lexeme
        
        type_annotation = None
        if self.match(TokenType.COLON):
            type_annotation = self.parse_type_annotation()
        
        return (name, type_annotation)
    
    def parse_class_declaration(self) -> ClassDeclarationNode:
        """Parse a 'vibe' class declaration.
        
        Grammar: vibe name [vibes_with parent] { fields and methods }
        """
        position = self.previous_token.position
        name = self.consume(TokenType.IDENTIFIER, "Expected class name").lexeme
        
        # Optional inheritance
        parent = None
        if self.match(TokenType.VIBES_WITH):
            parent = self.consume(TokenType.IDENTIFIER, "Expected parent class name").lexeme
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before class body")
        
        fields = []
        methods = []
        
        while not self.check(TokenType.RIGHT_BRACE) and not self.check(TokenType.EOF):
            # Skip newlines
            if self.match(TokenType.NEWLINE):
                continue
            
            # Field or method
            if self.match(TokenType.FR):
                fields.append(self.parse_variable_declaration())
            elif self.check(TokenType.LOWKEY) or self.check(TokenType.CHILL):
                methods.append(self.parse_function_declaration())
            else:
                self.error("Expected field or method declaration in class")
                self.advance()
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after class body")
        
        return ClassDeclarationNode(position, name, parent, fields, methods)
    
    def parse_enum_declaration(self) -> EnumDeclarationNode:
        """Parse a 'choices' enum declaration.
        
        Grammar: choices name { value1, value2, ... }
        """
        position = self.previous_token.position
        name = self.consume(TokenType.IDENTIFIER, "Expected enum name").lexeme
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before enum values")
        
        values = []
        values.append(self.consume(TokenType.IDENTIFIER, "Expected enum value").lexeme)
        
        while self.match(TokenType.COMMA):
            if self.check(TokenType.RIGHT_BRACE):
                break
            values.append(self.consume(TokenType.IDENTIFIER, "Expected enum value").lexeme)
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after enum values")
        
        return EnumDeclarationNode(position, name, values)
    
    def parse_print_statement(self) -> PrintStatementNode:
        """Parse a 'yap' print statement.
        
        Grammar: yap(expr1, expr2, ...)
        """
        position = self.previous_token.position
        
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'yap'")
        
        arguments = []
        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                arguments.append(self.parse_expression())
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments")
        
        return PrintStatementNode(position, arguments)
    
    def parse_if_statement(self) -> IfStatementNode:
        """Parse a 'vibecheck' if statement.
        
        Grammar: vibecheck condition { then_branch } [nah vibecheck condition { elif_branch }]* [nah { else_branch }]
        """
        position = self.previous_token.position
        
        condition = self.parse_expression()
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after condition")
        then_branch = self.parse_block()
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after then branch")
        
        elif_branches = []
        else_branch = None
        
        while self.match(TokenType.NAH):
            if self.match(TokenType.VIBECHECK):
                # Else-if branch
                elif_condition = self.parse_expression()
                self.consume(TokenType.LEFT_BRACE, "Expected '{' after condition")
                elif_body = self.parse_block()
                self.consume(TokenType.RIGHT_BRACE, "Expected '}' after elif branch")
                elif_branches.append((elif_condition, elif_body))
            else:
                # Else branch
                self.consume(TokenType.LEFT_BRACE, "Expected '{' after 'nah'")
                else_branch = self.parse_block()
                self.consume(TokenType.RIGHT_BRACE, "Expected '}' after else branch")
                break
        
        return IfStatementNode(position, condition, then_branch, elif_branches, else_branch)
    
    def parse_for_loop(self) -> ForLoopNode:
        """Parse a 'run' for loop.
        
        Grammar: run initializer; condition; increment { body }
        Example: run i: digits = 0; i < 10; i = i + 1 { ... }
        """
        position = self.previous_token.position
        
        # Initializer (required)
        initializer = None
        if self.match(TokenType.FR):
            initializer = self.parse_variable_declaration()
        elif self.check(TokenType.IDENTIFIER):
            # Could be variable declaration without 'fr' or assignment
            # Try to parse as variable declaration first
            name = self.consume(TokenType.IDENTIFIER, "Expected variable name").lexeme
            
            if self.match(TokenType.COLON):
                # Variable declaration: i: digits = 0
                type_annotation = self.parse_type_annotation()
                initializer_expr = None
                if self.match(TokenType.EQUAL):
                    initializer_expr = self.parse_expression()
                initializer = VariableDeclarationNode(position, name, type_annotation, initializer_expr)
            elif self.match(TokenType.EQUAL):
                # Assignment: i = 0
                value = self.parse_expression()
                initializer = AssignmentNode(position, IdentifierNode(position, name), value)
            else:
                self.error("Expected ':' or '=' in for loop initializer")
        
        self.consume(TokenType.SEMICOLON, "Expected ';' after for loop initializer")
        
        # Condition (required)
        condition = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after for loop condition")
        
        # Increment (required) - can be assignment or expression
        increment_expr = self.parse_expression()
        
        # Check if it's an assignment
        if self.match(TokenType.EQUAL):
            value = self.parse_expression()
            increment = AssignmentNode(position, increment_expr, value)
        else:
            increment = increment_expr
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before loop body")
        body = self.parse_block()
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after loop body")
        
        return ForLoopNode(position, initializer, condition, increment, body)

    
    def parse_while_loop(self) -> WhileLoopNode:
        """Parse an 'until' while loop.
        
        Grammar: until condition { body }
        """
        position = self.previous_token.position
        
        condition = self.parse_expression()
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before loop body")
        body = self.parse_block()
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after loop body")
        
        return WhileLoopNode(position, condition, body)
    
    def parse_foreach_loop(self) -> ForEachLoopNode:
        """Parse an 'each' for-each loop.
        
        Grammar: each variable [, key_variable] in iterable { body }
        """
        position = self.previous_token.position
        
        variable = self.consume(TokenType.IDENTIFIER, "Expected loop variable").lexeme
        
        # Optional key variable for bags
        key_variable = None
        if self.match(TokenType.COMMA):
            key_variable = self.consume(TokenType.IDENTIFIER, "Expected key variable").lexeme
        
        # 'in' keyword (using IDENTIFIER token)
        in_token = self.consume(TokenType.IDENTIFIER, "Expected 'in' keyword")
        if in_token.lexeme != "in":
            self.error("Expected 'in' keyword")
        
        iterable = self.parse_expression()
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before loop body")
        body = self.parse_block()
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after loop body")
        
        return ForEachLoopNode(position, variable, key_variable, iterable, body)
    
    def parse_return_statement(self) -> ReturnStatementNode:
        """Parse a 'comeback' return statement.
        
        Grammar: comeback [expression]
        """
        position = self.previous_token.position
        
        value = None
        if not self.check(TokenType.NEWLINE) and not self.check(TokenType.RIGHT_BRACE):
            value = self.parse_expression()
        
        return ReturnStatementNode(position, value)
    
    def parse_break_statement(self) -> BreakStatementNode:
        """Parse a 'dip' break statement."""
        position = self.previous_token.position
        return BreakStatementNode(position)
    
    def parse_continue_statement(self) -> ContinueStatementNode:
        """Parse a 'skip' continue statement."""
        position = self.previous_token.position
        return ContinueStatementNode(position)
    
    def parse_try_statement(self) -> TryStatementNode:
        """Parse a 'tryna' try-catch-finally statement.
        
        Grammar: tryna { try_block } [oops variable { catch_block }] [nomatter { finally_block }]
        """
        position = self.previous_token.position
        
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after 'tryna'")
        try_block = self.parse_block()
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after try block")
        
        catch_variable = None
        catch_block = None
        if self.match(TokenType.OOPS):
            catch_variable = self.consume(TokenType.IDENTIFIER, "Expected catch variable").lexeme
            self.consume(TokenType.LEFT_BRACE, "Expected '{' after catch variable")
            catch_block = self.parse_block()
            self.consume(TokenType.RIGHT_BRACE, "Expected '}' after catch block")
        
        finally_block = None
        if self.match(TokenType.NOMATTER):
            self.consume(TokenType.LEFT_BRACE, "Expected '{' after 'nomatter'")
            finally_block = self.parse_block()
            self.consume(TokenType.RIGHT_BRACE, "Expected '}' after finally block")
        
        return TryStatementNode(position, try_block, catch_variable, catch_block, finally_block)
    
    def parse_throw_statement(self) -> ThrowStatementNode:
        """Parse a 'crash' throw statement.
        
        Grammar: crash expression
        """
        position = self.previous_token.position
        expression = self.parse_expression()
        return ThrowStatementNode(position, expression)
    
    def parse_assert_statement(self) -> AssertStatementNode:
        """Parse a 'nocap' assert statement.
        
        Grammar: nocap(condition [, message])
        """
        position = self.previous_token.position
        
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'nocap'")
        condition = self.parse_expression()
        
        message = None
        if self.match(TokenType.COMMA):
            message = self.parse_expression()
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after assertion")
        
        return AssertStatementNode(position, condition, message)
    
    def parse_match_statement(self) -> MatchStatementNode:
        """Parse a 'match' pattern matching statement.
        
        Grammar: match expression { case pattern: body ... [default: body] }
        """
        position = self.previous_token.position
        
        expression = self.parse_expression()
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after match expression")
        
        cases = []
        default_case = None
        
        while not self.check(TokenType.RIGHT_BRACE) and not self.check(TokenType.EOF):
            # Skip newlines
            if self.match(TokenType.NEWLINE):
                continue
            
            if self.match(TokenType.HITS, TokenType.CASE):
                case_pos = self.previous_token.position
                pattern = self.parse_expression()
                
                # Optional guard
                guard = None
                if self.check(TokenType.IDENTIFIER) and self.current_token.lexeme == "if":
                    self.advance()
                    guard = self.parse_expression()
                
                self.consume(TokenType.COLON, "Expected ':' after case pattern")
                
                # Case body (single statement or block)
                case_body = []
                if self.match(TokenType.LEFT_BRACE):
                    case_body = self.parse_block()
                    self.consume(TokenType.RIGHT_BRACE, "Expected '}' after case body")
                else:
                    stmt = self.parse_statement()
                    if stmt:
                        case_body.append(stmt)
                
                cases.append(CaseNode(case_pos, pattern, guard, case_body))
            
            elif self.match(TokenType.OTHERWISE) or (self.check(TokenType.IDENTIFIER) and self.current_token.lexeme == "default"):
                if self.check(TokenType.IDENTIFIER):
                    self.advance()  # consume 'default'
                self.consume(TokenType.COLON, "Expected ':' after 'otherwise' or 'default'")
                
                # Default body
                if self.match(TokenType.LEFT_BRACE):
                    default_case = self.parse_block()
                    self.consume(TokenType.RIGHT_BRACE, "Expected '}' after default body")
                else:
                    stmt = self.parse_statement()
                    default_case = [stmt] if stmt else []
                break
            else:
                self.error("Expected 'hits'/'case' or 'otherwise'/'default' in check/match statement")
                self.advance()
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after match statement")
        
        return MatchStatementNode(position, expression, cases, default_case)
    
    def parse_expression_statement(self) -> Union[AssignmentNode, ExpressionStatementNode]:
        """Parse an expression statement or assignment.
        
        Grammar: expression | target = expression
        """
        position = self.current_token.position
        expr = self.parse_expression()
        
        # Check for assignment
        if self.match(TokenType.EQUAL):
            value = self.parse_expression()
            return AssignmentNode(position, expr, value)
        
        return ExpressionStatementNode(position, expr)
    
    def parse_block(self) -> List[StatementNode]:
        """Parse a block of statements (without braces)."""
        statements = []
        
        while not self.check(TokenType.RIGHT_BRACE) and not self.check(TokenType.EOF):
            # Skip newlines
            if self.match(TokenType.NEWLINE):
                continue
            
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        return statements
    
    # ========================================================================
    # Expression Parsing (Operator Precedence Climbing)
    # ========================================================================
    
    def parse_expression(self) -> ExpressionNode:
        """Parse an expression using operator precedence climbing."""
        return self.parse_or()
    
    def parse_or(self) -> ExpressionNode:
        """Parse logical OR expression."""
        expr = self.parse_and()
        
        while self.match(TokenType.OR):
            position = self.previous_token.position
            operator = "or"
            right = self.parse_and()
            expr = BinaryOpNode(position, expr, operator, right)
        
        return expr
    
    def parse_and(self) -> ExpressionNode:
        """Parse logical AND expression."""
        expr = self.parse_equality()
        
        while self.match(TokenType.AND):
            position = self.previous_token.position
            operator = "and"
            right = self.parse_equality()
            expr = BinaryOpNode(position, expr, operator, right)
        
        return expr
    
    def parse_equality(self) -> ExpressionNode:
        """Parse equality expression (==, !=)."""
        expr = self.parse_comparison()
        
        while self.match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            position = self.previous_token.position
            operator = self.previous_token.lexeme
            right = self.parse_comparison()
            expr = BinaryOpNode(position, expr, operator, right)
        
        return expr
    
    def parse_comparison(self) -> ExpressionNode:
        """Parse comparison expression (<, >, <=, >=)."""
        expr = self.parse_range()
        
        while self.match(TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            position = self.previous_token.position
            operator = self.previous_token.lexeme
            right = self.parse_range()
            expr = BinaryOpNode(position, expr, operator, right)
        
        return expr
    
    def parse_range(self) -> ExpressionNode:
        """Parse range expression (..)."""
        expr = self.parse_addition()
        
        if self.match(TokenType.DOTDOT):
            position = self.previous_token.position
            right = self.parse_addition()
            expr = BinaryOpNode(position, expr, '..', right)
        
        return expr
    
    def parse_addition(self) -> ExpressionNode:
        """Parse addition/subtraction expression (+, -)."""
        expr = self.parse_multiplication()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            position = self.previous_token.position
            operator = self.previous_token.lexeme
            right = self.parse_multiplication()
            expr = BinaryOpNode(position, expr, operator, right)
        
        return expr
    
    def parse_multiplication(self) -> ExpressionNode:
        """Parse multiplication/division/modulo expression (*, /, %)."""
        expr = self.parse_unary()
        
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            position = self.previous_token.position
            operator = self.previous_token.lexeme
            right = self.parse_unary()
            expr = BinaryOpNode(position, expr, operator, right)
        
        return expr
    
    def parse_unary(self) -> ExpressionNode:
        """Parse unary expression (-, not, holdup)."""
        if self.match(TokenType.MINUS, TokenType.NOT):
            position = self.previous_token.position
            operator = self.previous_token.lexeme
            operand = self.parse_unary()
            return UnaryOpNode(position, operator, operand)
        
        if self.match(TokenType.HOLDUP):
            position = self.previous_token.position
            expression = self.parse_unary()
            return AwaitNode(position, expression)
        
        return self.parse_postfix()

    
    def parse_postfix(self) -> ExpressionNode:
        """Parse postfix expression (calls, indexing, member access)."""
        expr = self.parse_primary()
        
        while True:
            if self.match(TokenType.LEFT_PAREN):
                # Function call
                position = self.previous_token.position
                arguments = []
                
                if not self.check(TokenType.RIGHT_PAREN):
                    arguments.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        arguments.append(self.parse_expression())
                
                self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments")
                expr = CallNode(position, expr, arguments)
            
            elif self.match(TokenType.LEFT_BRACKET):
                # Array/object indexing
                position = self.previous_token.position
                index = self.parse_expression()
                self.consume(TokenType.RIGHT_BRACKET, "Expected ']' after index")
                expr = IndexNode(position, expr, index)
            
            elif self.match(TokenType.DOT):
                # Member access
                position = self.previous_token.position
                member = self.consume(TokenType.IDENTIFIER, "Expected property name").lexeme
                expr = MemberAccessNode(position, expr, member)
            
            else:
                break
        
        return expr
    
    def parse_primary(self) -> ExpressionNode:
        """Parse primary expression (literals, identifiers, grouping)."""
        position = self.current_token.position
        
        # Literals
        if self.match(TokenType.REAL):
            return LiteralNode(position, True)
        
        if self.match(TokenType.FAKE):
            return LiteralNode(position, False)
        
        if self.match(TokenType.GHOST):
            return LiteralNode(position, None)
        
        if self.match(TokenType.NUMBER):
            return LiteralNode(position, self.previous_token.literal)
        
        if self.match(TokenType.STRING):
            return LiteralNode(position, self.previous_token.literal)
        
        # Identifier
        if self.match(TokenType.IDENTIFIER):
            return IdentifierNode(position, self.previous_token.lexeme)
        
        # Self
        if self.match(TokenType.SELF):
            return IdentifierNode(position, "self")
        
        # Array literal
        if self.match(TokenType.LEFT_BRACKET):
            return self.parse_array_literal()
        
        # Object literal
        if self.match(TokenType.LEFT_BRACE):
            return self.parse_object_literal()
        
        # Grouping
        if self.match(TokenType.LEFT_PAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return expr
        
        # Lambda function (anonymous function)
        # This would need special handling - for now, skip
        
        self.error(f"Unexpected token: {self.current_token.lexeme}")
        raise ParseError(f"Unexpected token: {self.current_token.lexeme}", position)
    
    def parse_array_literal(self) -> ArrayLiteralNode:
        """Parse an array literal.
        
        Grammar: [expr1, expr2, ...]
        """
        position = self.previous_token.position
        elements = []
        
        if not self.check(TokenType.RIGHT_BRACKET):
            elements.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RIGHT_BRACKET):
                    break
                elements.append(self.parse_expression())
        
        self.consume(TokenType.RIGHT_BRACKET, "Expected ']' after array elements")
        
        return ArrayLiteralNode(position, elements)
    
    def parse_object_literal(self) -> ObjectLiteralNode:
        """Parse an object literal.
        
        Grammar: { key1: value1, key2: value2, ... }
        """
        position = self.previous_token.position
        pairs = []
        
        if not self.check(TokenType.RIGHT_BRACE):
            # Parse first pair
            key = self.parse_expression()
            self.consume(TokenType.COLON, "Expected ':' after object key")
            value = self.parse_expression()
            pairs.append((key, value))
            
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RIGHT_BRACE):
                    break
                key = self.parse_expression()
                self.consume(TokenType.COLON, "Expected ':' after object key")
                value = self.parse_expression()
                pairs.append((key, value))
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after object pairs")
        
        return ObjectLiteralNode(position, pairs)
    
    # ========================================================================
    # Type Annotation Parsing
    # ========================================================================
    
    def parse_type_annotation(self) -> str:
        """Parse a type annotation.
        
        Grammar: type_name [< type_params >]
        
        Returns:
            String representation of the type (e.g., "digits", "lineup<text>")
        """
        # Simple type name
        if self.check(TokenType.TEXT):
            self.advance()
            return "text"
        elif self.check(TokenType.DIGITS):
            self.advance()
            return "digits"
        elif self.check(TokenType.TF):
            self.advance()
            return "tf"
        elif self.check(TokenType.VOID):
            self.advance()
            return "void"
        elif self.check(TokenType.LINEUP):
            self.advance()
            # Generic type parameter
            if self.match(TokenType.LESS):
                param = self.parse_type_annotation()
                self.consume(TokenType.GREATER, "Expected '>' after type parameter")
                return f"lineup<{param}>"
            return "lineup"
        elif self.check(TokenType.BAG):
            self.advance()
            # Generic type parameters
            if self.match(TokenType.LESS):
                key_type = self.parse_type_annotation()
                self.consume(TokenType.COMMA, "Expected ',' between bag type parameters")
                value_type = self.parse_type_annotation()
                self.consume(TokenType.GREATER, "Expected '>' after type parameters")
                return f"bag<{key_type}, {value_type}>"
            return "bag"
        elif self.check(TokenType.IDENTIFIER):
            # Custom type (class name)
            type_name = self.current_token.lexeme
            self.advance()
            return type_name
        else:
            self.error("Expected type annotation")
            return "unknown"
