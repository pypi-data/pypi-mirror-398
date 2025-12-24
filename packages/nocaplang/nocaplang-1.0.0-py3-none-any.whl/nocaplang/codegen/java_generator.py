"""Java code generator for NoCapLang.

This module generates Java 11+ code from a validated NoCapLang AST.
"""

from typing import List, Set, Optional
from ..parser.ast_nodes import *
from ..semantic.types import *


class JavaCodeGenerator:
    """Generates Java code from NoCapLang AST."""
    
    def __init__(self, ast: ProgramNode, class_name: str = "NoCapProgram"):
        """Initialize the Java code generator.
        
        Args:
            ast: The validated AST to generate code from
            class_name: Name of the main Java class to generate
        """
        self.ast = ast
        self.class_name = class_name
        self.indent_level = 0
        self.indent_str = "    "  # 4 spaces
        self.required_imports: Set[str] = set()
        self.in_class = False
        self.current_class_name: Optional[str] = None
        self.in_main = False
        
    def generate(self) -> str:
        """Generate complete Java code from the AST.
        
        Returns:
            Complete Java source code as a string
        """
        # Reset state
        self.indent_level = 0
        self.required_imports = set()
        
        # Always include basic imports
        self.required_imports.add("java.util.*")
        self.required_imports.add("java.io.*")
        
        # Separate class declarations from main code
        class_declarations = []
        function_declarations = []
        main_code = []
        
        for statement in self.ast.statements:
            if isinstance(statement, ClassDeclarationNode):
                class_declarations.append(statement)
            elif isinstance(statement, FunctionDeclarationNode):
                function_declarations.append(statement)
                # Check if function is async
                if statement.is_async:
                    self.required_imports.add("java.util.concurrent.*")
            else:
                main_code.append(statement)
        
        # Build final code
        code_parts = []
        
        # Add imports
        for import_stmt in sorted(self.required_imports):
            code_parts.append(f"import {import_stmt};")
        code_parts.append("")
        
        # Add main class
        code_parts.append(f"public class {self.class_name} {{")
        self.indent_level += 1
        
        # Add nested class declarations
        for class_decl in class_declarations:
            code = self.generate_statement(class_decl)
            if code:
                code_parts.append(code)
                code_parts.append("")
        
        # Add function declarations as static methods
        for func_decl in function_declarations:
            code = self.generate_statement(func_decl)
            if code:
                code_parts.append(code)
                code_parts.append("")
        
        # Add main method
        code_parts.append(f"{self._indent()}public static void main(String[] args) {{")
        self.indent_level += 1
        self.in_main = True
        
        # Add try-catch for error handling
        code_parts.append(f"{self._indent()}try {{")
        self.indent_level += 1
        
        # Add main code
        for statement in main_code:
            code = self.generate_statement(statement)
            if code:
                code_parts.append(code)
        
        self.indent_level -= 1
        code_parts.append(f"{self._indent()}}} catch (Exception e) {{")
        self.indent_level += 1
        code_parts.append(f'{self._indent()}System.err.println("Error: " + e.getMessage());')
        code_parts.append(f"{self._indent()}System.exit(1);")
        self.indent_level -= 1
        code_parts.append(f"{self._indent()}}}")
        
        self.in_main = False
        self.indent_level -= 1
        code_parts.append(f"{self._indent()}}}")
        
        self.indent_level -= 1
        code_parts.append("}")
        
        return "\n".join(code_parts)
    
    def _indent(self) -> str:
        """Get current indentation string."""
        return self.indent_str * self.indent_level
    
    def _mangle_name(self, name: str) -> str:
        """Mangle NoCapLang identifier to avoid Java keyword conflicts.
        
        Args:
            name: NoCapLang identifier
            
        Returns:
            Mangled Java identifier
        """
        # Java keywords that need mangling
        java_keywords = {
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
            'char', 'class', 'const', 'continue', 'default', 'do', 'double',
            'else', 'enum', 'extends', 'final', 'finally', 'float', 'for',
            'goto', 'if', 'implements', 'import', 'instanceof', 'int',
            'interface', 'long', 'native', 'new', 'package', 'private',
            'protected', 'public', 'return', 'short', 'static', 'strictfp',
            'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
            'transient', 'try', 'void', 'volatile', 'while', 'true', 'false',
            'null'
        }
        
        if name in java_keywords:
            return f"nocap_{name}"
        return name
    
    def _map_type(self, type_obj: Optional[Type]) -> str:
        """Map NoCapLang type to Java type.
        
        Args:
            type_obj: NoCapLang type object
            
        Returns:
            Java type string
        """
        if type_obj is None:
            return "Object"
        
        if isinstance(type_obj, PrimitiveType):
            type_map = {
                "text": "String",
                "digits": "double",
                "tf": "boolean",
                "void": "void",
                "ghost": "Object"
            }
            return type_map.get(type_obj.name, "Object")
        
        elif isinstance(type_obj, ArrayType):
            element_type = self._map_type(type_obj.element_type)
            return f"ArrayList<{self._box_primitive(element_type)}>"
        
        elif isinstance(type_obj, MapType):
            key_type = self._map_type(type_obj.key_type)
            value_type = self._map_type(type_obj.value_type)
            return f"HashMap<{self._box_primitive(key_type)}, {self._box_primitive(value_type)}>"
        
        elif isinstance(type_obj, FunctionType):
            # Java functional interfaces
            if len(type_obj.param_types) == 0:
                return_type = self._map_type(type_obj.return_type)
                if return_type == "void":
                    return "Runnable"
                else:
                    return f"Supplier<{self._box_primitive(return_type)}>"
            elif len(type_obj.param_types) == 1:
                param_type = self._map_type(type_obj.param_types[0])
                return_type = self._map_type(type_obj.return_type)
                if return_type == "void":
                    return f"Consumer<{self._box_primitive(param_type)}>"
                else:
                    return f"Function<{self._box_primitive(param_type)}, {self._box_primitive(return_type)}>"
            else:
                # For multiple parameters, use generic functional interface
                return "Object"
        
        elif isinstance(type_obj, ClassType):
            return self._mangle_name(type_obj.name)
        
        return "Object"
    
    def _box_primitive(self, java_type: str) -> str:
        """Convert primitive types to their boxed equivalents for generics.
        
        Args:
            java_type: Java type string
            
        Returns:
            Boxed type if primitive, otherwise original type
        """
        boxing_map = {
            "boolean": "Boolean",
            "byte": "Byte",
            "char": "Character",
            "short": "Short",
            "int": "Integer",
            "long": "Long",
            "float": "Float",
            "double": "Double"
        }
        return boxing_map.get(java_type, java_type)
    
    # ========================================================================
    # Statement Generation
    # ========================================================================
    
    def generate_statement(self, node: StatementNode) -> str:
        """Generate Java code for a statement node."""
        return node.accept(self)
    
    def visit_variable_declaration(self, node: VariableDeclarationNode) -> str:
        """Generate Java code for variable declaration."""
        name = self._mangle_name(node.name)
        
        if node.type_annotation:
            # Parse type annotation
            type_obj = parse_type_annotation(node.type_annotation)
            java_type = self._map_type(type_obj)
        elif hasattr(node, 'expr_type') and node.expr_type:
            java_type = self._map_type(node.expr_type)
        else:
            java_type = "Object"
        
        # Add optimization hints
        hints = ""
        if hasattr(node, 'java_hints') and 'final' in node.java_hints:
            hints = "final "
        
        if node.initializer:
            value = self.generate_expression(node.initializer)
            return f"{self._indent()}{hints}{java_type} {name} = {value};"
        else:
            # Initialize to null/default
            if java_type in ["boolean", "byte", "char", "short", "int", "long", "float", "double"]:
                return f"{self._indent()}{hints}{java_type} {name} = 0;"
            else:
                return f"{self._indent()}{hints}{java_type} {name} = null;"
    
    def visit_assignment(self, node: AssignmentNode) -> str:
        """Generate Java code for assignment."""
        target = self.generate_expression(node.target)
        value = self.generate_expression(node.value)
        return f"{self._indent()}{target} = {value};"
    
    def visit_expression_statement(self, node: ExpressionStatementNode) -> str:
        """Generate Java code for expression statement."""
        expr = self.generate_expression(node.expression)
        return f"{self._indent()}{expr};"
    
    def visit_print_statement(self, node: PrintStatementNode) -> str:
        """Generate Java code for print statement (yap)."""
        if not node.arguments:
            return f'{self._indent()}System.out.println();'
        
        # Build print statement
        if len(node.arguments) == 1:
            expr = self.generate_expression(node.arguments[0])
            return f'{self._indent()}System.out.println({expr});'
        else:
            # Multiple arguments - concatenate with spaces
            parts = []
            for arg in node.arguments:
                expr = self.generate_expression(arg)
                parts.append(expr)
            
            output = ' + " " + '.join(parts)
            return f'{self._indent()}System.out.println({output});'
    
    def visit_if_statement(self, node: IfStatementNode) -> str:
        """Generate Java code for if statement (vibecheck)."""
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
        """Generate Java code for for loop (run)."""
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
            increment = self.generate_expression(node.increment)
        
        lines.append(f"{self._indent()}for ({init}; {condition}; {increment}) {{")
        self.indent_level += 1
        for stmt in node.body:
            lines.append(self.generate_statement(stmt))
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_while_loop(self, node: WhileLoopNode) -> str:
        """Generate Java code for while loop (until)."""
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
        """Generate Java code for foreach loop (each)."""
        lines = []
        
        var_name = self._mangle_name(node.variable)
        iterable = self.generate_expression(node.iterable)
        
        if node.key_variable:
            # Iterating over map with key and value
            key_name = self._mangle_name(node.key_variable)
            lines.append(f"{self._indent()}for (var entry : {iterable}.entrySet()) {{")
            self.indent_level += 1
            lines.append(f"{self._indent()}var {key_name} = entry.getKey();")
            lines.append(f"{self._indent()}var {var_name} = entry.getValue();")
            for stmt in node.body:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        else:
            # Iterating over array
            lines.append(f"{self._indent()}for (var {var_name} : {iterable}) {{")
            self.indent_level += 1
            for stmt in node.body:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_return_statement(self, node: ReturnStatementNode) -> str:
        """Generate Java code for return statement (comeback)."""
        if node.value:
            value = self.generate_expression(node.value)
            return f"{self._indent()}return {value};"
        return f"{self._indent()}return;"
    
    def visit_break_statement(self, node: BreakStatementNode) -> str:
        """Generate Java code for break statement (dip)."""
        return f"{self._indent()}break;"
    
    def visit_continue_statement(self, node: ContinueStatementNode) -> str:
        """Generate Java code for continue statement (skip)."""
        return f"{self._indent()}continue;"
    
    def visit_try_statement(self, node: TryStatementNode) -> str:
        """Generate Java code for try-catch statement (tryna/oops/nomatter)."""
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
            lines.append(f"{self._indent()}catch (Exception {catch_var}) {{")
            self.indent_level += 1
            for stmt in node.catch_block:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        # Finally block
        if node.finally_block:
            lines.append(f"{self._indent()}finally {{")
            self.indent_level += 1
            for stmt in node.finally_block:
                lines.append(self.generate_statement(stmt))
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_throw_statement(self, node: ThrowStatementNode) -> str:
        """Generate Java code for throw statement (crash)."""
        message = self.generate_expression(node.expression)
        return f'{self._indent()}throw new RuntimeException({message});'
    
    def visit_assert_statement(self, node: AssertStatementNode) -> str:
        """Generate Java code for assert statement (nocap)."""
        condition = self.generate_expression(node.condition)
        
        if node.message:
            message = self.generate_expression(node.message)
            # Use if statement to throw exception with message
            lines = []
            lines.append(f"{self._indent()}if (!({condition})) {{")
            self.indent_level += 1
            lines.append(f'{self._indent()}throw new AssertionError("Assertion failed: " + {message});')
            self.indent_level -= 1
            lines.append(f"{self._indent()}}}")
            return "\n".join(lines)
        else:
            return f"{self._indent()}assert {condition};"
    
    def visit_function_declaration(self, node: FunctionDeclarationNode) -> str:
        """Generate Java code for function declaration (lowkey)."""
        lines = []
        
        # Determine return type
        if node.return_type:
            return_type_obj = parse_type_annotation(node.return_type)
            return_type = self._map_type(return_type_obj)
        else:
            return_type = "Object"
        
        # Handle async functions
        if node.is_async:
            # Note: imports are added during generate() phase
            return_type = f"CompletableFuture<{self._box_primitive(return_type)}>"
        
        # Build parameter list
        params = []
        for param_name, param_type in node.parameters:
            mangled_name = self._mangle_name(param_name)
            if param_type:
                type_obj = parse_type_annotation(param_type)
                java_type = self._map_type(type_obj)
                params.append(f"{java_type} {mangled_name}")
            else:
                params.append(f"Object {mangled_name}")
        
        param_str = ", ".join(params)
        func_name = self._mangle_name(node.name)
        
        # Add static modifier if in main class
        modifier = "static " if self.in_main or not self.in_class else ""
        
        # Function signature
        lines.append(f"{self._indent()}{modifier}{return_type} {func_name}({param_str}) {{")
        self.indent_level += 1
        
        # For async functions, wrap in CompletableFuture
        if node.is_async:
            lines.append(f"{self._indent()}return CompletableFuture.supplyAsync(() -> {{")
            self.indent_level += 1
        
        # Function body
        for stmt in node.body:
            lines.append(self.generate_statement(stmt))
        
        # Close async wrapper
        if node.is_async:
            self.indent_level -= 1
            lines.append(f"{self._indent()}}});")
        
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        
        return "\n".join(lines)
    
    def visit_class_declaration(self, node: ClassDeclarationNode) -> str:
        """Generate Java code for class declaration (vibe)."""
        lines = []
        
        class_name = self._mangle_name(node.name)
        self.in_class = True
        self.current_class_name = class_name
        
        # Class declaration
        modifier = "static " if self.in_main else ""
        if node.parent:
            parent_name = self._mangle_name(node.parent)
            lines.append(f"{self._indent()}{modifier}class {class_name} extends {parent_name} {{")
        else:
            lines.append(f"{self._indent()}{modifier}class {class_name} {{")
        
        self.indent_level += 1
        
        # Fields
        for field in node.fields:
            field_code = self.generate_statement(field)
            lines.append(field_code)
        
        # Methods
        for method in node.methods:
            method_code = self.generate_statement(method)
            lines.append(method_code)
        
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        
        self.in_class = False
        self.current_class_name = None
        
        return "\n".join(lines)
    
    def visit_match_statement(self, node: MatchStatementNode) -> str:
        """Generate Java code for match statement."""
        lines = []
        
        # Generate expression to match
        match_expr = self.generate_expression(node.expression)
        match_var = f"_matchValue{id(node)}"
        lines.append(f"{self._indent()}var {match_var} = {match_expr};")
        
        # Generate if-else chain for cases
        first_case = True
        for case in node.cases:
            pattern = self.generate_expression(case.pattern)
            
            # Build condition using Objects.equals for null safety
            condition = f"Objects.equals({match_var}, {pattern})"
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
        """Generate Java code for import statement (grab)."""
        # For now, we'll just add a comment
        # Full import support would require a module system
        return f"{self._indent()}// Import: {node.path}"
    
    def visit_enum_declaration(self, node: EnumDeclarationNode) -> str:
        """Generate Java code for enum declaration (choices)."""
        lines = []
        enum_name = self._mangle_name(node.name)
        modifier = "static " if self.in_main else ""
        lines.append(f"{self._indent()}{modifier}enum {enum_name} {{")
        self.indent_level += 1
        for i, value in enumerate(node.values):
            comma = "," if i < len(node.values) - 1 else ""
            lines.append(f"{self._indent()}{value}{comma}")
        self.indent_level -= 1
        lines.append(f"{self._indent()}}}")
        return "\n".join(lines)
    
    # ========================================================================
    # Expression Generation
    # ========================================================================
    
    def generate_expression(self, node: ExpressionNode) -> str:
        """Generate Java code for an expression node."""
        return node.accept(self)
    
    def visit_literal(self, node: LiteralNode) -> str:
        """Generate Java code for literal."""
        value = node.value
        
        if value is None:
            return "null"
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
        """Generate Java code for identifier."""
        # Handle special identifiers
        if node.name == "self":
            return "this"
        return self._mangle_name(node.name)
    
    def visit_binary_op(self, node: BinaryOpNode) -> str:
        """Generate Java code for binary operation."""
        left = self.generate_expression(node.left)
        right = self.generate_expression(node.right)
        
        # Map NoCapLang operators to Java
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
            "*": "*",
            "/": "/",
            "%": "%"
        }
        
        java_op = op_map.get(node.operator, node.operator)
        return f"({left} {java_op} {right})"
    
    def visit_unary_op(self, node: UnaryOpNode) -> str:
        """Generate Java code for unary operation."""
        operand = self.generate_expression(node.operand)
        
        op_map = {
            "not": "!",
            "-": "-",
            "+": "+"
        }
        
        java_op = op_map.get(node.operator, node.operator)
        return f"({java_op}{operand})"
    
    def visit_call(self, node: CallNode) -> str:
        """Generate Java code for function call."""
        callee = self.generate_expression(node.callee)
        args = [self.generate_expression(arg) for arg in node.arguments]
        args_str = ", ".join(args)
        return f"{callee}({args_str})"
    
    def visit_index(self, node: IndexNode) -> str:
        """Generate Java code for indexing."""
        obj = self.generate_expression(node.object)
        index = self.generate_expression(node.index)
        
        # For ArrayList, use get() method; for HashMap, use get()
        # We'll use get() for both since it works for both types
        return f"{obj}.get((int){index})"
    
    def visit_member_access(self, node: MemberAccessNode) -> str:
        """Generate Java code for member access."""
        obj = self.generate_expression(node.object)
        return f"{obj}.{node.member}"
    
    def visit_array_literal(self, node: ArrayLiteralNode) -> str:
        """Generate Java code for array literal."""
        elements = [self.generate_expression(elem) for elem in node.elements]
        
        # Create ArrayList with elements
        if elements:
            elements_str = ", ".join(elements)
            return f"new ArrayList<>(Arrays.asList({elements_str}))"
        else:
            return "new ArrayList<>()"
    
    def visit_object_literal(self, node: ObjectLiteralNode) -> str:
        """Generate Java code for object literal."""
        lines = []
        
        # Create HashMap and populate it
        map_var = f"_map{id(node)}"
        lines.append(f"new HashMap<>() {{{{")
        
        # Use initializer block
        for key, value in node.pairs:
            key_str = self.generate_expression(key)
            value_str = self.generate_expression(value)
            lines.append(f" put({key_str}, {value_str});")
        
        lines.append("}}")
        
        return "".join(lines)
    
    def visit_lambda(self, node: LambdaNode) -> str:
        """Generate Java code for lambda function."""
        # Build parameter list
        params = []
        for param_name, param_type in node.parameters:
            mangled_name = self._mangle_name(param_name)
            params.append(mangled_name)
        
        param_str = ", ".join(params) if params else "()"
        if len(params) == 1:
            param_str = params[0]
        else:
            param_str = f"({', '.join(params)})"
        
        # Generate body - for simplicity, we'll use a block lambda
        body_lines = []
        for stmt in node.body:
            body_lines.append(self.generate_statement(stmt))
        body_str = "\n".join(body_lines)
        
        return f"{param_str} -> {{\n{body_str}\n{self._indent()}}}"
    
    def visit_await(self, node: AwaitNode) -> str:
        """Generate Java code for await expression (holdup)."""
        # Note: imports are added during generate() phase
        expr = self.generate_expression(node.expression)
        return f"{expr}.join()"
    
    def visit_new(self, node: NewNode) -> str:
        """Generate Java code for class instantiation."""
        class_name = self._mangle_name(node.class_name)
        args = [self.generate_expression(arg) for arg in node.arguments]
        args_str = ", ".join(args)
        return f"new {class_name}({args_str})"
    
    def visit_case(self, node: CaseNode) -> str:
        """Generate Java code for case node (used in match)."""
        # This is handled by visit_match_statement
        return ""
    
    def visit_program(self, node: ProgramNode) -> str:
        """Generate Java code for program node."""
        # This is handled by generate()
        return ""
