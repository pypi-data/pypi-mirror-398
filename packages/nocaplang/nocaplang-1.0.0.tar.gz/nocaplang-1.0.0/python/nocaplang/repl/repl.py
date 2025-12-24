"""Interactive REPL for NoCapLang.

This module provides a Read-Eval-Print Loop for interactive NoCapLang development.
"""

import sys
from typing import Optional, List, Dict, Any
from enum import Enum

from ..compiler import Compiler, Target, CompilationResult
from ..lexer.lexer import Lexer
from ..parser.parser import Parser
from ..parser.ast_nodes import (
    ExpressionStatementNode, 
    VariableDeclarationNode,
    FunctionDeclarationNode,
    ClassDeclarationNode
)
from ..semantic.analyzer import SemanticAnalyzer


class REPLCommand(Enum):
    """Special REPL commands."""
    EXIT = ":exit"
    QUIT = ":quit"
    HELP = ":help"
    CLEAR = ":clear"
    TYPE = ":type"
    TARGET = ":target"


class REPL:
    """Interactive Read-Eval-Print Loop for NoCapLang."""
    
    def __init__(self, target: Target = Target.CPP):
        """Initialize the REPL.
        
        Args:
            target: Target language for code generation
        """
        self.target = target
        self.compiler = Compiler(target=target, verbose=False)
        self.state: Dict[str, Any] = {}  # Store variables and functions
        self.history: List[str] = []  # Command history
        self.accumulated_code: List[str] = []  # Accumulated declarations
        
    def start(self) -> None:
        """Start the REPL loop."""
        self._print_welcome()
        
        while True:
            try:
                # Read input
                line = self._read_input()
                
                if not line.strip():
                    continue
                
                # Check for special commands
                if line.startswith(':'):
                    if not self._handle_command(line):
                        break  # Exit command
                    continue
                
                # Add to history
                self.history.append(line)
                
                # Check if input is complete
                if self._is_incomplete(line):
                    # Multi-line input
                    full_input = self._read_multiline(line)
                else:
                    full_input = line
                
                # Evaluate the input
                self._evaluate(full_input)
                
            except KeyboardInterrupt:
                print("\n(Use :exit or :quit to exit)")
                continue
            except EOFError:
                print("\nGoodbye!")
                break
    
    def evaluate(self, input_str: str) -> Optional[str]:
        """Evaluate a single input string (for testing).
        
        Args:
            input_str: Input string to evaluate
            
        Returns:
            Result string or None
        """
        return self._evaluate(input_str)
    
    def _print_welcome(self) -> None:
        """Print welcome message."""
        print("NoCapLang REPL v0.1.0")
        print(f"Target: {self.target.value.upper()}")
        print("Type ':help' for help, ':exit' or ':quit' to exit")
        print()
    
    def _read_input(self) -> str:
        """Read a line of input from the user.
        
        Returns:
            Input line
        """
        try:
            return input(">>> ")
        except EOFError:
            raise
    
    def _read_multiline(self, first_line: str) -> str:
        """Read multi-line input.
        
        Args:
            first_line: First line of input
            
        Returns:
            Complete multi-line input
        """
        lines = [first_line]
        
        while True:
            try:
                line = input("... ")
                lines.append(line)
                
                # Check if input is now complete
                full_input = '\n'.join(lines)
                if not self._is_incomplete(full_input):
                    break
                    
            except EOFError:
                break
        
        return '\n'.join(lines)
    
    def _is_incomplete(self, code: str) -> bool:
        """Check if the input is incomplete (needs more lines).
        
        Args:
            code: Code to check
            
        Returns:
            True if incomplete, False otherwise
        """
        # Simple heuristic: check for unclosed braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        
        if open_braces > close_braces:
            return True
        
        # Check for incomplete statements (ends with certain keywords)
        stripped = code.strip()
        incomplete_endings = [
            'vibecheck', 'nah', 'run', 'until', 'each', 
            'lowkey', 'vibe', 'tryna', 'oops', 'nomatter',
            'match', 'case', 'chill'
        ]
        
        for ending in incomplete_endings:
            if stripped.endswith(ending):
                return True
        
        return False
    
    def _handle_command(self, command: str) -> bool:
        """Handle special REPL commands.
        
        Args:
            command: Command string
            
        Returns:
            True to continue REPL, False to exit
        """
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd in [REPLCommand.EXIT.value, REPLCommand.QUIT.value]:
            print("Goodbye!")
            return False
        
        elif cmd == REPLCommand.HELP.value:
            self._print_help()
        
        elif cmd == REPLCommand.CLEAR.value:
            self._clear_state()
            print("State cleared.")
        
        elif cmd == REPLCommand.TYPE.value:
            if len(parts) < 2:
                print("Usage: :type <expression>")
            else:
                expr = ' '.join(parts[1:])
                self._show_type(expr)
        
        elif cmd == REPLCommand.TARGET.value:
            if len(parts) < 2:
                print(f"Current target: {self.target.value}")
                print("Usage: :target <cpp|java>")
            else:
                new_target = parts[1].lower()
                if new_target == "cpp":
                    self.target = Target.CPP
                    self.compiler = Compiler(target=Target.CPP, verbose=False)
                    print("Target set to C++")
                elif new_target == "java":
                    self.target = Target.JAVA
                    self.compiler = Compiler(target=Target.JAVA, verbose=False)
                    print("Target set to Java")
                else:
                    print(f"Unknown target: {new_target}")
                    print("Available targets: cpp, java")
        
        else:
            print(f"Unknown command: {cmd}")
            print("Type ':help' for available commands")
        
        return True
    
    def _print_help(self) -> None:
        """Print help message."""
        print("""
NoCapLang REPL Commands:
  :exit, :quit     Exit the REPL
  :help            Show this help message
  :clear           Clear all variables and state
  :type <expr>     Show the type of an expression
  :target [lang]   Show or set compilation target (cpp or java)

You can enter NoCapLang expressions and statements.
Multi-line input is supported - the REPL will prompt for continuation.
        """.strip())
    
    def _clear_state(self) -> None:
        """Clear REPL state."""
        self.state.clear()
        self.accumulated_code.clear()
    
    def _show_type(self, expr: str) -> None:
        """Show the type of an expression.
        
        Args:
            expr: Expression to type-check
        """
        try:
            # Wrap in a program context with accumulated declarations
            full_code = '\n'.join(self.accumulated_code) + '\n' + expr
            
            # Compile to get type information
            lexer = Lexer(full_code, "<repl>")
            parser = Parser(lexer)
            ast = parser.parse_program()
            
            if parser.errors:
                print(f"Parse error: {parser.errors[0].message}")
                return
            
            analyzer = SemanticAnalyzer(ast)
            annotated_ast, errors = analyzer.analyze()
            
            if errors:
                print(f"Type error: {errors[0].message}")
                return
            
            # Get the last statement (our expression)
            if annotated_ast.statements:
                last_stmt = annotated_ast.statements[-1]
                if hasattr(last_stmt, 'expression') and hasattr(last_stmt.expression, 'expr_type'):
                    print(f"Type: {last_stmt.expression.expr_type}")
                else:
                    print("Unable to determine type")
            else:
                print("No expression found")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def _evaluate(self, code: str) -> Optional[str]:
        """Evaluate NoCapLang code.
        
        Args:
            code: Code to evaluate
            
        Returns:
            Result string or None
        """
        try:
            # Parse the input to determine what it is
            lexer = Lexer(code, "<repl>")
            parser = Parser(lexer)
            ast = parser.parse_program()
            
            if parser.errors:
                for error in parser.errors:
                    print(f"Parse error: {error.message}")
                return None
            
            # Check if this is a declaration (variable, function, class)
            is_declaration = False
            if ast.statements:
                first_stmt = ast.statements[0]
                if isinstance(first_stmt, (VariableDeclarationNode, 
                                          FunctionDeclarationNode, 
                                          ClassDeclarationNode)):
                    is_declaration = True
            
            # Build full program with accumulated state
            if is_declaration:
                # Add to accumulated code
                self.accumulated_code.append(code)
                full_program = '\n'.join(self.accumulated_code)
            else:
                # For expressions/statements, wrap with accumulated declarations
                full_program = '\n'.join(self.accumulated_code)
                if full_program:
                    full_program += '\n'
                full_program += code
            
            # Compile the full program
            result = self.compiler.compile_string(full_program, "<repl>")
            
            if not result.success:
                for error in result.errors:
                    print(error)
                return None
            
            # For expressions, try to evaluate and display result
            if not is_declaration and ast.statements:
                first_stmt = ast.statements[0]
                if isinstance(first_stmt, ExpressionStatementNode):
                    # This is an expression - we'd need to execute it to show result
                    # For now, just indicate success
                    print(self._colorize("✓", "green"))
                else:
                    # Statement executed
                    print(self._colorize("✓", "green"))
            else:
                # Declaration added
                print(self._colorize("✓", "green"))
            
            return result.code
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def _colorize(self, text: str, color: str) -> str:
        """Add color to text (if terminal supports it).
        
        Args:
            text: Text to colorize
            color: Color name
            
        Returns:
            Colorized text
        """
        # ANSI color codes
        colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'reset': '\033[0m'
        }
        
        if sys.stdout.isatty() and color in colors:
            return f"{colors[color]}{text}{colors['reset']}"
        return text


def start_repl(target: Target = Target.CPP) -> None:
    """Start the REPL.
    
    Args:
        target: Target language for compilation
    """
    repl = REPL(target=target)
    repl.start()
