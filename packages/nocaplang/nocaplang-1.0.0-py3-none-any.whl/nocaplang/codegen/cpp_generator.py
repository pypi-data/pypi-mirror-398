"""C++ code generator for NoCapLang.

This module generates C++17 code from a validated NoCapLang AST.
"""

from typing import List, Set, Optional
from ..parser.ast_nodes import *
from ..semantic.types import *


class CppCodeGenerator:
    """Generates C++ code from NoCapLang AST."""
    
    def __init__(self, ast: ProgramNode):
        """Initialize the C++ code generator.
        
        Args:
            ast: The validated AST to generate code from
        """
        self.ast = ast
        self.indent_level = 0
        self.indent_str = "    "  # 4 spaces
        self.required_headers: Set[str] = set()
        self.in_class = False
        self.current_class_name: Optional[str] = None
        
    def generate(self) -> str:
        """Generate complete C++ code from the AST.
        
        Returns:
            Complete C++ source code as a string
        """
        # Reset state
        self.indent_level = 0
        self.required_headers = set()
        
        # Always include basic headers
        self.required_headers.add("iostream")
        self.required_headers.add("string")
        self.required_headers.add("memory")
        self.required_headers.add("stdexcept")
        
        # Separate functions/classes from main code
        functions = []
        classes = []
        main_code = []
        
        for statement in self.ast.statements:
            if isinstance(statement, FunctionDeclarationNode):
                functions.append(statement)
            elif isinstance(statement, ClassDeclarationNode):
                classes.append(statement)
            else:
                main_code.append(statement)
        
        # First pass: generate all code to collect required headers
        temp_function_code = []
        temp_class_code = []
        temp_main_code = []
        
        for class_node in classes:
            temp_class_code.append(self.generate_statement(class_node))
        
        for func_node in functions:
            temp_function_code.append(self.generate_statement(func_node))
        
        for statement in main_code:
            code = self.generate_statement(statement)
            if code:
                temp_main_code.append(code)
        
        # Now build final code with all collected headers
        code_parts = []
        
        # Add stdlib header first
        code_parts.append('// NoCapLang Standard Library')
        code_parts.append('#include "nocaplang_stdlib.hpp"')
        code_parts.append("")
        
        # Add other headers
        for header in sorted(self.required_headers):
            code_parts.append(f"#include <{header}>")
        code_parts.append("")
        
        # Add using namespace std for convenience
        code_parts.append("using namespace std;")
        code_parts.append("")
        
        # Add forward declarations for classes
        for class_node in classes:
            class_name = self._mangle_name(class_node.name)
            code_parts.append(f"class {class_name};")
        if classes:
            code_parts.append("")
        
        # Add class definitions
        for class_code in temp_class_code:
            code_parts.append(class_code)
            code_parts.append("")
        
        # Add function declarations
        for func_code in temp_function_code:
            code_parts.append(func_code)
            code_parts.append("")
        
        # Add main function wrapper
        code_parts.append("int main() {")
        self.indent_level += 1
        
        # Add try-catch for error handling
        code_parts.append(self._indent() + "try {")
        self.indent_level += 1
        
        # Enable boolalpha for printing true/false instead of 1/0
        code_parts.append(self._indent() + "cout << boolalpha;")
        code_parts.append("")
        
        # Add main code body
        for code in temp_main_code:
            code_parts.append(code)
        
        # Return success
        code_parts.append(self._indent() + "return 0;")
        
        self.indent_level -= 1
        code_parts.append(self._indent() + "} catch (const exception& e) {")
        self.indent_level += 1
        code_parts.append(self._indent() + 'cerr << "Error: " << e.what() << endl;')
        code_parts.append(self._indent() + "return 1;")
        self.indent_level -= 1
        code_parts.append(self._indent() + "}")
        
        self.indent_level -= 1
        code_parts.append("}")
        
        return "\n".join(code_parts)
    
    def _indent(self) -> str:
        """Get current indentation string."""
        return self.indent_str * self.indent_level
    
    def _mangle_name(self, name: str) -> str:
        """Mangle NoCapLang identifier to avoid C++ keyword conflicts.
        
        Args:
            name: NoCapLang identifier
            
        Returns:
            Mangled C++ identifier
        """
        # C++ keywords that need mangling
        cpp_keywords = {
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default',
            'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto',
            'if', 'int', 'long', 'register', 'return', 'short', 'signed',
            'sizeof', 'static', 'struct', 'switch', 'typedef', 'union',
            'unsigned', 'void', 'volatile', 'while', 'class', 'namespace',
            'template', 'typename', 'using', 'virtual', 'private', 'protected',
            'public', 'friend', 'inline', 'operator', 'this', 'throw', 'try',
            'catch', 'new', 'delete', 'true', 'false', 'nullptr'
        }
        
        if name in cpp_keywords:
            return f"nocap_{name}"
        return name
    
    def _map_type(self, type_obj: Optional[Type]) -> str:
        """Map NoCapLang type to C++ type.
        
        Args:
            type_obj: NoCapLang type object
            
        Returns:
            C++ type string
        """
        if type_obj is None:
            return "auto"
        
        if isinstance(type_obj, PrimitiveType):
            type_map = {
                "text": "string",
                "digits": "double",
                "tf": "bool",
                "void": "void",
                "ghost": "std::any"  # Use std::any for ghost type to support heterogeneous collections
            }
            mapped = type_map.get(type_obj.name, "auto")
            if mapped == "std::any":
                self.required_headers.add("any")
            return mapped
        
        elif isinstance(type_obj, ArrayType):
            self.required_headers.add("vector")
            element_type = self._map_type(type_obj.element_type)
            return f"vector<{element_type}>"
        
        elif isinstance(type_obj, MapType):
            self.required_headers.add("unordered_map")
            key_type = self._map_type(type_obj.key_type)
            value_type = self._map_type(type_obj.value_type)
            return f"unordered_map<{key_type}, {value_type}>"
        
        elif isinstance(type_obj, FunctionType):
            self.required_headers.add("functional")
            param_types = ", ".join(self._map_type(p) for p in type_obj.param_types)
            return_type = self._map_type(type_obj.return_type)
            return f"function<{return_type}({param_types})>"
        
        elif isinstance(type_obj, ClassType):
            return self._mangle_name(type_obj.name)
        
        return "auto"
    
    # ========================================================================
    # Statement Generation
    # ========================================================================
    
    def generate_statement(self, node: StatementNode) -> str:
        """Generate C++ code for a statement node."""
        return node.accept(self)
    
    def visit_variable_declaration(self, node: VariableDeclarationNode) -> str:
        """Generate C++ code for variable declaration."""
        name = self._mangle_name(node.name)
        
        if node.type_annotation:
            # Parse type annotation
            type_obj = parse_type_annotation(node.type_annotation)
            cpp_type = self._map_type(type_obj)
        elif hasattr(node, 'expr_type') and node.expr_type:
            cpp_type = self._map_type(node.expr_type)
        else:
            cpp_type = "auto"
        
        if node.initializer:
            value = self.generate_expression(node.initializer)
            return f"{self._indent()}{cpp_type} {name} = {value};"
        else:
            # Initialize to nullptr/default
            if cpp_type == "auto":
                return f"{self._indent()}nullptr_t {name} = nullptr;"
            return f"{self._indent()}{cpp_type} {name}{{}};"
    
    def visit_assignment(self, node: AssignmentNode) -> str:
        """Generate C++ code for assignment."""
        target = self.generate_expression(node.target)
        value = self.generate_expression(node.value)
        return f"{self._indent()}{target} = {value};"
    
    def visit_expression_statement(self, node: ExpressionStatementNode) -> str:
        """Generate C++ code for expression statement."""
        expr = self.generate_expression(node.expression)
        return f"{self._indent()}{expr};"
    
    def visit_print_statement(self, node: PrintStatementNode) -> str:
        """Generate C++ code for print statement (yap)."""
        if not node.arguments:
            return f'{self._indent()}cout << endl;'
        
        parts = []
        for i, arg in enumerate(node.arguments):
            expr = self.generate_expression(arg)
            parts.append(expr)
            if i < len(node.arguments) - 1:
                parts.append('" "')
        
        output = " << ".join(parts)
        return f'{self._indent()}cout << {output} << endl;'
    
    def visit_if_statement(self, node: IfStatementNode) -> str:
        """Generate C++ code for if statement (vibecheck)."""
        lines = []
        
        # Main if
        condition = self.generate_expression(node.condition)
        lines.append(f"{self._indent()}if ({condition}) {{")
        self.indent_level += 1
        for stmt in node.then_branch:
            lines.append(self.generate_statement(stmt))
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        
        # Elif branches
        for elif_cond, elif_body in node.elif_branches:
            elif_condition = self.generate_expression(elif_cond)
            lines.append(f"{self._indent()}else if ({elif_condition}) {{")
            self.indent_level += 1
            for stmt in elif_body:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        # Else branch
        if node.else_branch:
            lines.append(f"{self._indent()}else {{")
            self.indent_level += 1
            for stmt in node.else_branch:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_for_loop(self, node: ForLoopNode) -> str:
        """Generate C++ code for for loop (run)."""
        lines = []
        
        # Build for loop components
        init = ""
        if node.initializer:
            init_code = self.generate_statement(node.initializer)
            # Remove indent and semicolon
            init = init_code.strip().rstrip(';')
        
        condition = self.generate_expression(node.condition) if node.condition else "true"
        
        increment = ""
        if node.increment:
            # Check if increment is an assignment (statement) or expression
            if isinstance(node.increment, AssignmentNode):
                # Generate as expression (without semicolon)
                target = self.generate_expression(node.increment.target)
                value = self.generate_expression(node.increment.value)
                increment = f"{target} = {value}"
            else:
                # Generate as expression
                increment = self.generate_expression(node.increment)
        
        lines.append(f"{self._indent()}for ({init}; {condition}; {increment}) {{")
        self.indent_level += 1
        for stmt in node.body:
            lines.append(self.generate_statement(stmt))
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_while_loop(self, node: WhileLoopNode) -> str:
        """Generate C++ code for while loop (until)."""
        lines = []
        condition = self.generate_expression(node.condition)
        lines.append(f"{self._indent()}while ({condition}) {{")
        self.indent_level += 1
        for stmt in node.body:
            lines.append(self.generate_statement(stmt))
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        return "\n".join(lines)
    
    def visit_foreach_loop(self, node: ForEachLoopNode) -> str:
        """Generate C++ code for foreach loop (each)."""
        self.required_headers.add("vector")
        lines = []
        
        var_name = self._mangle_name(node.variable)
        iterable = self.generate_expression(node.iterable)
        
        if node.key_variable:
            # Iterating over map with key and value: each key, value in map
            key_name = self._mangle_name(node.key_variable)
            lines.append(f"{self._indent()}for (auto& [{key_name}, {var_name}] : {iterable}) {{")
        else:
            # Check if iterating over a map (need to extract key from pair)
            # For maps, the iterator gives us pair<key, value>, so we extract .first
            if hasattr(node, 'iterable') and hasattr(node.iterable, 'expr_type'):
                if isinstance(node.iterable.expr_type, MapType):
                    # Iterating over map keys only
                    lines.append(f"{self._indent()}for (auto& _pair : {iterable}) {{")
                    self.indent_level += 1
                    lines.append(f"{self._indent()}auto& {var_name} = _pair.first;")
                    self.indent_level -= 1
                    # Don't close brace yet, will be added after body
                else:
                    # Iterating over array
                    lines.append(f"{self._indent()}for (auto& {var_name} : {iterable}) {{")
            else:
                # Default: iterate over array
                lines.append(f"{self._indent()}for (auto& {var_name} : {iterable}) {{")
        
        self.indent_level += 1
        for stmt in node.body:
            lines.append(self.generate_statement(stmt))
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_return_statement(self, node: ReturnStatementNode) -> str:
        """Generate C++ code for return statement (comeback)."""
        if node.value:
            value = self.generate_expression(node.value)
            return f"{self._indent()}return {value};"
        return f"{self._indent()}return;"
    
    def visit_break_statement(self, node: BreakStatementNode) -> str:
        """Generate C++ code for break statement (dip)."""
        return f"{self._indent()}break;"
    
    def visit_continue_statement(self, node: ContinueStatementNode) -> str:
        """Generate C++ code for continue statement (skip)."""
        return f"{self._indent()}continue;"
    
    def visit_try_statement(self, node: TryStatementNode) -> str:
        """Generate C++ code for try-catch statement (tryna/oops/nomatter)."""
        lines = []
        
        # Try block
        lines.append(f"{self._indent()}try {{")
        self.indent_level += 1
        for stmt in node.try_block:
            lines.append(self.generate_statement(stmt))
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        
        # Catch block
        if node.catch_block:
            catch_var = self._mangle_name(node.catch_variable) if node.catch_variable else "e"
            lines.append(f"{self._indent()}catch (const exception& {catch_var}) {{")
            self.indent_level += 1
            for stmt in node.catch_block:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        # Finally block (using RAII pattern)
        if node.finally_block:
            # C++ doesn't have finally, but we can simulate with a scope guard
            self.required_headers.add("functional")
            lines.append(f"{self._indent()}{{")
            self.indent_level += 1
            lines.append(f"{self._indent()}// Finally block")
            for stmt in node.finally_block:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_throw_statement(self, node: ThrowStatementNode) -> str:
        """Generate C++ code for throw statement (crash)."""
        message = self.generate_expression(node.expression)
        return f'{self._indent()}throw runtime_error({message});'
    
    def visit_assert_statement(self, node: AssertStatementNode) -> str:
        """Generate C++ code for assert statement (nocap)."""
        self.required_headers.add("cassert")
        condition = self.generate_expression(node.condition)
        
        if node.message:
            message = self.generate_expression(node.message)
            # C++ assert doesn't support messages, so we throw if condition fails
            lines = []
            lines.append(f"{self._indent()}if (!({condition})) {{")
            self.indent_level += 1
            lines.append(f'{self._indent()}throw runtime_error(string("Assertion failed: ") + {message});')
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
            return "\n".join(lines)
        else:
            return f"{self._indent()}assert({condition});"
    
    def visit_function_declaration(self, node: FunctionDeclarationNode) -> str:
        """Generate C++ code for function declaration (lowkey)."""
        lines = []
        
        # Determine return type
        if node.return_type:
            return_type_obj = parse_type_annotation(node.return_type)
            return_type = self._map_type(return_type_obj)
        else:
            return_type = "auto"
        
        # Handle async functions
        actual_return_type = return_type
        if node.is_async:
            self.required_headers.add("future")
            actual_return_type = f"future<{return_type}>"
        
        # Build parameter list
        params = []
        for param_name, param_type in node.parameters:
            mangled_name = self._mangle_name(param_name)
            if param_type:
                type_obj = parse_type_annotation(param_type)
                cpp_type = self._map_type(type_obj)
                params.append(f"{cpp_type} {mangled_name}")
            else:
                params.append(f"auto {mangled_name}")
        
        param_str = ", ".join(params)
        func_name = self._mangle_name(node.name)
        
        # Add optimization hints
        hints = ""
        if hasattr(node, 'cpp_hints') and 'inline' in node.cpp_hints:
            hints = "inline "
        
        # Function signature
        lines.append(f"{self._indent()}{hints}{actual_return_type} {func_name}({param_str}) {{")
        self.indent_level += 1
        
        if node.is_async:
            # Wrap async function body in std::async
            lines.append(f"{self._indent()}return std::async(std::launch::async, [=]() -> {return_type} {{")
            self.indent_level += 1
        
        # Function body
        for stmt in node.body:
            lines.append(self.generate_statement(stmt))
        
        if node.is_async:
            self.indent_level -= 1
            lines.append(f"{self._indent()}}});")
        
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_class_declaration(self, node: ClassDeclarationNode) -> str:
        """Generate C++ code for class declaration (vibe)."""
        lines = []
        
        class_name = self._mangle_name(node.name)
        self.in_class = True
        self.current_class_name = class_name
        
        # Class declaration
        if node.parent:
            parent_name = self._mangle_name(node.parent)
            lines.append(f"{self._indent()}class {class_name} : public {parent_name} {{")
        else:
            lines.append(f"{self._indent()}class {class_name} {{")
        
        lines.append(f"{self._indent()}public:")
        self.indent_level += 1
        
        # Fields
        for field in node.fields:
            field_code = self.generate_statement(field)
            lines.append(field_code)
        
        # Generate constructor from init method (if exists)
        init_method = None
        for method in node.methods:
            if method.name == "init":
                init_method = method
                break
        
        if init_method:
            # Only add default constructor if init has parameters (for inheritance support)
            if len(init_method.parameters) > 0:
                lines.append(f"{self._indent()}{class_name}() = default;")
            
            # Build constructor parameter list
            params = []
            for param_name, param_type in init_method.parameters:
                mangled_name = self._mangle_name(param_name)
                if param_type:
                    type_obj = parse_type_annotation(param_type)
                    cpp_type = self._map_type(type_obj)
                    params.append(f"{cpp_type} {mangled_name}")
                else:
                    params.append(f"auto {mangled_name}")
            
            param_str = ", ".join(params)
            
            # Constructor signature
            lines.append(f"{self._indent()}{class_name}({param_str}) {{")
            self.indent_level += 1
            
            # Constructor body (from init method)
            for stmt in init_method.body:
                lines.append(self.generate_statement(stmt))
            
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        # Other methods (excluding init)
        for method in node.methods:
            if method.name != "init":
                method_code = self.generate_statement(method)
                lines.append(method_code)
        
        self.indent_level -= 1
        lines.append(f"{self._indent()}}};")
        
        self.in_class = False
        self.current_class_name = None
        
        return "\n".join(lines)
    
    def visit_match_statement(self, node: MatchStatementNode) -> str:
        """Generate C++ code for match statement."""
        lines = []
        
        # Generate expression to match
        match_expr = self.generate_expression(node.expression)
        match_var = f"_match_value_{id(node)}"
        lines.append(f"{self._indent()}auto {match_var} = {match_expr};")
        
        # Generate if-else chain for cases
        first_case = True
        for case in node.cases:
            # Check if pattern is a range (BinaryOpNode with '..' operator)
            if isinstance(case.pattern, BinaryOpNode) and case.pattern.operator == '..':
                # Range pattern: generate range check
                range_start = self.generate_expression(case.pattern.left)
                range_end = self.generate_expression(case.pattern.right)
                condition = f"({match_var} >= {range_start} && {match_var} <= {range_end})"
            else:
                # Regular pattern: generate equality check
                pattern = self.generate_expression(case.pattern)
                condition = f"{match_var} == {pattern}"
            
            # Add guard if present
            if case.guard:
                guard_expr = self.generate_expression(case.guard)
                condition = f"({condition}) && ({guard_expr})"
            
            if first_case:
                lines.append(f"{self._indent()}if ({condition}) {{")
                first_case = False
            else:
                lines.append(f"{self._indent()}else if ({condition}) {{")
            
            self.indent_level += 1
            for stmt in case.body:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        # Default case
        if node.default_case:
            lines.append(f"{self._indent()}else {{")
            self.indent_level += 1
            for stmt in node.default_case:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_import(self, node: ImportNode) -> str:
        """Generate C++ code for import statement (grab)."""
        # For now, we'll just add a comment
        # Full import support would require a module system
        return f"{self._indent()}// Import: {node.path}"
    
    def visit_enum_declaration(self, node: EnumDeclarationNode) -> str:
        """Generate C++ code for enum declaration (choices)."""
        lines = []
        enum_name = self._mangle_name(node.name)
        lines.append(f"{self._indent()}enum class {enum_name} {{")
        self.indent_level += 1
        for i, value in enumerate(node.values):
            comma = "," if i < len(node.values) - 1 else ""
            lines.append(f"{self._indent()}{value}{comma}")
        self.indent_level -= 1
        lines.append(f"{self._indent()}}};")
        return "\n".join(lines)
    
    # ========================================================================
    # Expression Generation
    # ========================================================================
    
    def generate_expression(self, node: ExpressionNode) -> str:
        """Generate C++ code for an expression node."""
        return node.accept(self)
    
    def visit_literal(self, node: LiteralNode) -> str:
        """Generate C++ code for literal."""
        value = node.value
        
        if value is None:
            return "null_value"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # Escape string
            escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
            return f'"{escaped}"'
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)
    
    def visit_identifier(self, node: IdentifierNode) -> str:
        """Generate C++ code for identifier."""
        # Handle special identifiers
        if node.name == "self":
            return "this"
        return self._mangle_name(node.name)
    
    def visit_binary_op(self, node: BinaryOpNode) -> str:
        """Generate C++ code for binary operation."""
        left = self.generate_expression(node.left)
        right = self.generate_expression(node.right)
        
        # Special handling for + operator with text types (string concatenation)
        if node.operator == '+':
            # Check if this is string concatenation
            left_is_text = (hasattr(node.left, 'expr_type') and 
                           node.left.expr_type is not None and 
                           node.left.expr_type.is_compatible_with(TEXT_TYPE))
            right_is_text = (hasattr(node.right, 'expr_type') and 
                            node.right.expr_type is not None and 
                            node.right.expr_type.is_compatible_with(TEXT_TYPE))
            
            if left_is_text or right_is_text:
                # String concatenation - convert both to text
                if not left_is_text:
                    left = f"to_text({left})"
                if not right_is_text:
                    right = f"to_text({right})"
                return f"({left} + {right})"
        
        # Special handling for division (use safe_divide to throw on divide by zero)
        if node.operator == '/':
            return f"safe_divide({left}, {right})"
        
        # Special handling for modulo operator (use fmod for doubles)
        if node.operator == '%':
            self.required_headers.add("cmath")
            return f"std::fmod({left}, {right})"
        
        # Map NoCapLang operators to C++
        op_map = {
            "and": "&&",
            "or": "||",
            "==": "==",
            "!=": "!=",
            "<": "<",
            ">": ">",
            "<=": "<=",
            ">=": ">=",
            "+": "+",
            "-": "-",
            "*": "*"
        }
        
        cpp_op = op_map.get(node.operator, node.operator)
        return f"({left} {cpp_op} {right})"
    
    def visit_unary_op(self, node: UnaryOpNode) -> str:
        """Generate C++ code for unary operation."""
        operand = self.generate_expression(node.operand)
        
        op_map = {
            "not": "!",
            "-": "-",
            "+": "+"
        }
        
        cpp_op = op_map.get(node.operator, node.operator)
        return f"({cpp_op}{operand})"
    
    def visit_call(self, node: CallNode) -> str:
        """Generate C++ code for function call."""
        callee = self.generate_expression(node.callee)
        args = [self.generate_expression(arg) for arg in node.arguments]
        args_str = ", ".join(args)
        
        # Check if this is an async function call (returns future)
        # If called from non-async context, automatically await it
        if hasattr(node, 'expr_type') and isinstance(node.expr_type, FunctionType):
            if node.expr_type.is_async:
                # Async function - need to call .get() to await
                return f"{callee}({args_str}).get()"
        
        return f"{callee}({args_str})"
    
    def visit_index(self, node: IndexNode) -> str:
        """Generate C++ code for indexing."""
        obj = self.generate_expression(node.object)
        index = self.generate_expression(node.index)
        return f"{obj}[{index}]"
    
    def visit_member_access(self, node: MemberAccessNode) -> str:
        """Generate C++ code for member access."""
        obj = self.generate_expression(node.object)
        
        # Handle pointer vs value access
        if self.in_class and obj == "this":
            return f"this->{node.member}"
        return f"{obj}.{node.member}"
    
    def visit_array_literal(self, node: ArrayLiteralNode) -> str:
        """Generate C++ code for array literal."""
        self.required_headers.add("vector")
        elements = [self.generate_expression(elem) for elem in node.elements]
        elements_str = ", ".join(elements)
        
        # Determine element type if available
        if hasattr(node, 'expr_type') and isinstance(node.expr_type, ArrayType):
            elem_type = self._map_type(node.expr_type.element_type)
            return f"vector<{elem_type}>{{{elements_str}}}"
        return f"vector<auto>{{{elements_str}}}"
    
    def visit_object_literal(self, node: ObjectLiteralNode) -> str:
        """Generate C++ code for object literal."""
        self.required_headers.add("unordered_map")
        
        # Determine types if available
        if hasattr(node, 'expr_type') and isinstance(node.expr_type, MapType):
            key_type = self._map_type(node.expr_type.key_type)
            value_type = self._map_type(node.expr_type.value_type)
            
            # If value type is std::any, wrap values
            if value_type == "std::any":
                pairs = []
                for key, value in node.pairs:
                    key_str = self.generate_expression(key)
                    value_str = self.generate_expression(value)
                    pairs.append(f"{{{key_str}, std::any({value_str})}}")
                pairs_str = ", ".join(pairs)
            else:
                pairs = []
                for key, value in node.pairs:
                    key_str = self.generate_expression(key)
                    value_str = self.generate_expression(value)
                    pairs.append(f"{{{key_str}, {value_str}}}")
                pairs_str = ", ".join(pairs)
            
            return f"unordered_map<{key_type}, {value_type}>{{{pairs_str}}}"
        
        # Fallback
        pairs = []
        for key, value in node.pairs:
            key_str = self.generate_expression(key)
            value_str = self.generate_expression(value)
            pairs.append(f"{{{key_str}, {value_str}}}")
        pairs_str = ", ".join(pairs)
        return f"unordered_map<auto, auto>{{{pairs_str}}}"
    
    def visit_lambda(self, node: LambdaNode) -> str:
        """Generate C++ code for lambda function."""
        # Build parameter list
        params = []
        for param_name, param_type in node.parameters:
            mangled_name = self._mangle_name(param_name)
            if param_type:
                type_obj = parse_type_annotation(param_type)
                cpp_type = self._map_type(type_obj)
                params.append(f"{cpp_type} {mangled_name}")
            else:
                params.append(f"auto {mangled_name}")
        
        param_str = ", ".join(params)
        
        # Generate body
        body_lines = []
        for stmt in node.body:
            body_lines.append(self.generate_statement(stmt))
        body_str = "\n".join(body_lines)
        
        return f"[&]({param_str}) {{\n{body_str}\n{self._indent()}}}"
    
    def visit_await(self, node: AwaitNode) -> str:
        """Generate C++ code for await expression (holdup)."""
        self.required_headers.add("future")
        expr = self.generate_expression(node.expression)
        return f"{expr}.get()"
    
    def visit_new(self, node: NewNode) -> str:
        """Generate C++ code for class instantiation."""
        self.required_headers.add("memory")
        class_name = self._mangle_name(node.class_name)
        args = [self.generate_expression(arg) for arg in node.arguments]
        args_str = ", ".join(args)
        return f"make_shared<{class_name}>({args_str})"
    
    def visit_case(self, node: CaseNode) -> str:
        """Generate C++ code for case node (used in match)."""
        # This is handled by visit_match_statement
        return ""
    
    def visit_program(self, node: ProgramNode) -> str:
        """Generate C++ code for program node."""
        # This is handled by generate()
        return ""
