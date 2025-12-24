"""Example AST constructions for NoCapLang syntax.

This file demonstrates how NoCapLang source code maps to AST nodes.
"""

from .ast_nodes import *
from ..lexer.token import Position


def example_variable_declaration():
    """
    NoCapLang: fr x: digits = 42
    """
    pos = Position("example.nocap", 1, 1)
    return VariableDeclarationNode(
        position=pos,
        name="x",
        type_annotation="digits",
        initializer=LiteralNode(pos, 42)
    )


def example_function_declaration():
    """
    NoCapLang:
    lowkey add(a: digits, b: digits): digits {
        comeback a + b
    }
    """
    pos = Position("example.nocap", 1, 1)
    return FunctionDeclarationNode(
        position=pos,
        name="add",
        parameters=[("a", "digits"), ("b", "digits")],
        body=[
            ReturnStatementNode(
                position=pos,
                value=BinaryOpNode(
                    position=pos,
                    left=IdentifierNode(pos, "a"),
                    operator="+",
                    right=IdentifierNode(pos, "b")
                )
            )
        ],
        return_type="digits",
        is_async=False
    )


def example_if_statement():
    """
    NoCapLang:
    vibecheck x > 10 {
        yap("x is large")
    } nah {
        yap("x is small")
    }
    """
    pos = Position("example.nocap", 1, 1)
    return IfStatementNode(
        position=pos,
        condition=BinaryOpNode(
            position=pos,
            left=IdentifierNode(pos, "x"),
            operator=">",
            right=LiteralNode(pos, 10)
        ),
        then_branch=[
            PrintStatementNode(
                position=pos,
                arguments=[LiteralNode(pos, "x is large")]
            )
        ],
        elif_branches=[],
        else_branch=[
            PrintStatementNode(
                position=pos,
                arguments=[LiteralNode(pos, "x is small")]
            )
        ]
    )


def example_for_loop():
    """
    NoCapLang:
    run (fr i = 0; i < 10; i = i + 1) {
        yap(i)
    }
    """
    pos = Position("example.nocap", 1, 1)
    return ForLoopNode(
        position=pos,
        initializer=VariableDeclarationNode(
            position=pos,
            name="i",
            type_annotation=None,
            initializer=LiteralNode(pos, 0)
        ),
        condition=BinaryOpNode(
            position=pos,
            left=IdentifierNode(pos, "i"),
            operator="<",
            right=LiteralNode(pos, 10)
        ),
        increment=AssignmentNode(
            position=pos,
            target=IdentifierNode(pos, "i"),
            value=BinaryOpNode(
                position=pos,
                left=IdentifierNode(pos, "i"),
                operator="+",
                right=LiteralNode(pos, 1)
            )
        ),
        body=[
            PrintStatementNode(
                position=pos,
                arguments=[IdentifierNode(pos, "i")]
            )
        ]
    )


def example_class_declaration():
    """
    NoCapLang:
    vibe Person {
        fr name: text
        fr age: digits
        
        lowkey greet() {
            yap("Hello, I'm", self.name)
        }
    }
    """
    pos = Position("example.nocap", 1, 1)
    return ClassDeclarationNode(
        position=pos,
        name="Person",
        parent=None,
        fields=[
            VariableDeclarationNode(pos, "name", "text", None),
            VariableDeclarationNode(pos, "age", "digits", None)
        ],
        methods=[
            FunctionDeclarationNode(
                position=pos,
                name="greet",
                parameters=[],
                body=[
                    PrintStatementNode(
                        position=pos,
                        arguments=[
                            LiteralNode(pos, "Hello, I'm"),
                            MemberAccessNode(
                                position=pos,
                                object=IdentifierNode(pos, "self"),
                                member="name"
                            )
                        ]
                    )
                ],
                return_type=None,
                is_async=False
            )
        ]
    )


def example_try_catch():
    """
    NoCapLang:
    tryna {
        fr result = risky_operation()
    } oops e {
        yap("Error:", e)
    } nomatter {
        yap("Cleanup")
    }
    """
    pos = Position("example.nocap", 1, 1)
    return TryStatementNode(
        position=pos,
        try_block=[
            VariableDeclarationNode(
                position=pos,
                name="result",
                type_annotation=None,
                initializer=CallNode(
                    position=pos,
                    callee=IdentifierNode(pos, "risky_operation"),
                    arguments=[]
                )
            )
        ],
        catch_variable="e",
        catch_block=[
            PrintStatementNode(
                position=pos,
                arguments=[
                    LiteralNode(pos, "Error:"),
                    IdentifierNode(pos, "e")
                ]
            )
        ],
        finally_block=[
            PrintStatementNode(
                position=pos,
                arguments=[LiteralNode(pos, "Cleanup")]
            )
        ]
    )


def example_array_and_indexing():
    """
    NoCapLang:
    fr numbers: lineup<digits> = [1, 2, 3, 4, 5]
    fr first = numbers[0]
    """
    pos = Position("example.nocap", 1, 1)
    return [
        VariableDeclarationNode(
            position=pos,
            name="numbers",
            type_annotation="lineup<digits>",
            initializer=ArrayLiteralNode(
                position=pos,
                elements=[
                    LiteralNode(pos, 1),
                    LiteralNode(pos, 2),
                    LiteralNode(pos, 3),
                    LiteralNode(pos, 4),
                    LiteralNode(pos, 5)
                ]
            )
        ),
        VariableDeclarationNode(
            position=pos,
            name="first",
            type_annotation=None,
            initializer=IndexNode(
                position=pos,
                object=IdentifierNode(pos, "numbers"),
                index=LiteralNode(pos, 0)
            )
        )
    ]


def example_match_statement():
    """
    NoCapLang:
    match value {
        case 0: yap("zero")
        case 1: yap("one")
        default: yap("other")
    }
    """
    pos = Position("example.nocap", 1, 1)
    return MatchStatementNode(
        position=pos,
        expression=IdentifierNode(pos, "value"),
        cases=[
            CaseNode(
                position=pos,
                pattern=LiteralNode(pos, 0),
                guard=None,
                body=[PrintStatementNode(pos, [LiteralNode(pos, "zero")])]
            ),
            CaseNode(
                position=pos,
                pattern=LiteralNode(pos, 1),
                guard=None,
                body=[PrintStatementNode(pos, [LiteralNode(pos, "one")])]
            )
        ],
        default_case=[
            PrintStatementNode(pos, [LiteralNode(pos, "other")])
        ]
    )


if __name__ == "__main__":
    # Demonstrate creating AST nodes
    print("NoCapLang AST Examples\n")
    
    print("1. Variable Declaration:")
    var = example_variable_declaration()
    print(f"   {var.name}: {var.type_annotation} = {var.initializer.value}\n")
    
    print("2. Function Declaration:")
    func = example_function_declaration()
    print(f"   {func.name}({', '.join(f'{p[0]}: {p[1]}' for p in func.parameters)}): {func.return_type}\n")
    
    print("3. If Statement:")
    if_stmt = example_if_statement()
    print(f"   Condition: {if_stmt.condition.operator}")
    print(f"   Then branch: {len(if_stmt.then_branch)} statement(s)")
    print(f"   Else branch: {len(if_stmt.else_branch)} statement(s)\n")
    
    print("4. Class Declaration:")
    cls = example_class_declaration()
    print(f"   {cls.name}")
    print(f"   Fields: {len(cls.fields)}")
    print(f"   Methods: {len(cls.methods)}\n")
    
    print("✅ All examples created successfully!")
