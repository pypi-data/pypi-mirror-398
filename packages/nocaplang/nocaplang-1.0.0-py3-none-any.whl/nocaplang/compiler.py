"""Main compiler driver for NoCapLang.

This module orchestrates the compilation pipeline:
Lexer -> Parser -> Semantic Analyzer -> Code Generator
"""

import sys
from pathlib import Path
from typing import Optional, List
from enum import Enum

from .lexer.lexer import Lexer, LexerError
from .lexer.token import Position
from .parser.parser import Parser, ParseError
from .parser.ast_nodes import ProgramNode
from .semantic.analyzer import SemanticAnalyzer, SemanticError
from .optimizer.optimizer import Optimizer
from .codegen.cpp_generator import CppCodeGenerator
from .codegen.java_generator import JavaCodeGenerator
from .error_formatter import (
    format_lexer_error, format_parse_error, format_semantic_error,
    format_compilation_errors
)


class Target(Enum):
    """Compilation target languages."""
    CPP = "cpp"
    JAVA = "java"


class CompilationError(Exception):
    """Exception raised during compilation."""
    
    def __init__(self, message: str, position: Optional[Position] = None):
        self.message = message
        self.position = position
        if position:
            super().__init__(f"{position}: {message}")
        else:
            super().__init__(message)


class CompilationResult:
    """Result of a compilation."""
    
    def __init__(self, success: bool, code: Optional[str] = None, 
                 errors: Optional[List[str]] = None):
        self.success = success
        self.code = code
        self.errors = errors or []
    
    def __bool__(self):
        return self.success


class Compiler:
    """Main compiler class that orchestrates the compilation pipeline."""
    
    def __init__(self, target: Target = Target.CPP, verbose: bool = False, use_color: bool = True, optimize: bool = True):
        """Initialize the compiler.
        
        Args:
            target: Target language for code generation
            verbose: Enable verbose output
            use_color: Enable colored error messages
            optimize: Enable optimization passes
        """
        self.target = target
        self.verbose = verbose
        self.use_color = use_color
        self.optimize = optimize
    
    def compile_file(self, input_path: Path, output_path: Optional[Path] = None) -> CompilationResult:
        """Compile a NoCapLang source file.
        
        Args:
            input_path: Path to input .nocap file
            output_path: Path to output file (optional, will be auto-generated if not provided)
            
        Returns:
            CompilationResult with success status and generated code or errors
        """
        # Validate input file
        if not input_path.exists():
            return CompilationResult(
                success=False,
                errors=[f"File not found: {input_path}"]
            )
        
        # Read source code
        try:
            source_code = input_path.read_text(encoding='utf-8')
        except Exception as e:
            return CompilationResult(
                success=False,
                errors=[f"Failed to read file {input_path}: {e}"]
            )
        
        # Compile the source code
        result = self.compile_string(source_code, str(input_path))
        
        # Write output if compilation succeeded
        if result.success and output_path:
            try:
                output_path.write_text(result.code, encoding='utf-8')
                if self.verbose:
                    print(f"Generated code written to: {output_path}")
            except Exception as e:
                return CompilationResult(
                    success=False,
                    errors=[f"Failed to write output file {output_path}: {e}"]
                )
        
        return result
    
    def compile_string(self, source: str, filename: str = "<input>") -> CompilationResult:
        """Compile NoCapLang source code from a string.
        
        Args:
            source: NoCapLang source code
            filename: Filename for error reporting
            
        Returns:
            CompilationResult with success status and generated code or errors
        """
        errors = []
        
        try:
            # Stage 1: Lexical Analysis
            if self.verbose:
                print("Stage 1: Lexical Analysis...")
            
            lexer = Lexer(source, filename)
            tokens = lexer.scan_tokens()
            
            if self.verbose:
                print(f"  Generated {len(tokens)} tokens")
            
            # Stage 2: Parsing
            if self.verbose:
                print("Stage 2: Parsing...")
            
            parser = Parser(lexer)
            ast = parser.parse_program()
            
            # Check for parse errors
            if parser.errors:
                for error in parser.errors:
                    formatted = format_parse_error(error, source, self.use_color)
                    errors.append(formatted)
                return CompilationResult(success=False, errors=errors)
            
            if self.verbose:
                print(f"  Parsed {len(ast.statements)} statements")
            
            # Stage 3: Semantic Analysis
            if self.verbose:
                print("Stage 3: Semantic Analysis...")
            
            analyzer = SemanticAnalyzer(ast)
            annotated_ast, semantic_errors = analyzer.analyze()
            
            # Check for semantic errors
            if semantic_errors:
                for error in semantic_errors:
                    formatted = format_semantic_error(error, source, self.use_color)
                    errors.append(formatted)
                return CompilationResult(success=False, errors=errors)
            
            if self.verbose:
                print("  Semantic analysis passed")
            
            # Stage 3.5: Optimization (if enabled)
            if self.optimize:
                if self.verbose:
                    print("Stage 3.5: Optimization...")
                
                optimizer = Optimizer(annotated_ast, self.target.value)
                annotated_ast = optimizer.optimize()
                
                if self.verbose:
                    optimizations = optimizer.get_optimizations_applied()
                    if optimizations:
                        print(f"  Applied {len(optimizations)} optimizations")
                        for opt in optimizations[:5]:  # Show first 5
                            print(f"    - {opt}")
                        if len(optimizations) > 5:
                            print(f"    ... and {len(optimizations) - 5} more")
                    else:
                        print("  No optimizations applied")
            
            # Stage 4: Code Generation
            if self.verbose:
                print(f"Stage 4: Code Generation ({self.target.value})...")
            
            if self.target == Target.CPP:
                generator = CppCodeGenerator(annotated_ast)
            else:  # Target.JAVA
                # Extract class name from filename
                class_name = Path(filename).stem.replace('-', '_').replace('.', '_')
                # Capitalize first letter
                class_name = class_name[0].upper() + class_name[1:] if class_name else "NoCapProgram"
                generator = JavaCodeGenerator(annotated_ast, class_name)
            
            generated_code = generator.generate()
            
            if self.verbose:
                print(f"  Generated {len(generated_code)} characters of {self.target.value} code")
            
            return CompilationResult(success=True, code=generated_code)
            
        except LexerError as e:
            formatted = format_lexer_error(e, source, self.use_color)
            errors.append(formatted)
            return CompilationResult(success=False, errors=errors)
        
        except ParseError as e:
            formatted = format_parse_error(e, source, self.use_color)
            errors.append(formatted)
            return CompilationResult(success=False, errors=errors)
        
        except Exception as e:
            # Catch any unexpected errors
            errors.append(f"Internal compiler error: {e}")
            if self.verbose:
                import traceback
                errors.append(traceback.format_exc())
            return CompilationResult(success=False, errors=errors)
    
    def _format_error(self, message: str, position: Position, source: str) -> str:
        """Format an error message with source code context.
        
        Args:
            message: Error message
            position: Position of the error
            source: Source code
            
        Returns:
            Formatted error message with context
        """
        lines = source.split('\n')
        
        # Build error message
        error_parts = [f"Error at {position}: {message}"]
        
        # Add source context if available
        if 0 < position.line <= len(lines):
            line_num = position.line
            line = lines[line_num - 1]
            
            # Show the line with error
            error_parts.append(f"  {line_num:4d} | {line}")
            
            # Show error marker
            if position.column > 0:
                marker = " " * (7 + position.column - 1) + "^"
                error_parts.append(marker)
        
        return "\n".join(error_parts)
    
    def get_default_output_path(self, input_path: Path) -> Path:
        """Get default output path based on input path and target.
        
        Args:
            input_path: Input file path
            
        Returns:
            Default output file path
        """
        if self.target == Target.CPP:
            return input_path.with_suffix('.cpp')
        else:  # Target.JAVA
            # For Java, use the stem as class name
            class_name = input_path.stem.replace('-', '_').replace('.', '_')
            class_name = class_name[0].upper() + class_name[1:] if class_name else "NoCapProgram"
            return input_path.with_name(f"{class_name}.java")
