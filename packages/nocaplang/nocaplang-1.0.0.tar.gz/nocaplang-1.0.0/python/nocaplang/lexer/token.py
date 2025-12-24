"""Token and TokenType definitions for NoCapLang lexer."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    """Token types for NoCapLang."""
    
    # Keywords
    FR = auto()              # fr (variable declaration)
    YAP = auto()             # yap (print)
    VIBECHECK = auto()       # vibecheck (if)
    NAH = auto()             # nah (else)
    RUN = auto()             # run (for loop)
    UNTIL = auto()           # until (while loop)
    EACH = auto()            # each (for-each loop)
    LOWKEY = auto()          # lowkey (function)
    COMEBACK = auto()        # comeback (return)
    DIP = auto()             # dip (break)
    SKIP = auto()            # skip (continue)
    TRYNA = auto()           # tryna (try)
    OOPS = auto()            # oops (catch)
    NOMATTER = auto()        # nomatter (finally)
    CRASH = auto()           # crash (throw)
    VIBE = auto()            # vibe (class)
    VIBES_WITH = auto()      # vibes_with (extends)
    SELF = auto()            # self
    CHILL = auto()           # chill (async)
    HOLDUP = auto()          # holdup (await)
    MATCH = auto()           # match (deprecated - use CHECK)
    CHECK = auto()           # check (pattern matching)
    CASE = auto()            # case (deprecated - use HITS)
    HITS = auto()            # hits (pattern case)
    OTHERWISE = auto()       # otherwise (default case)
    GRAB = auto()            # grab (import)
    NOCAP = auto()           # nocap (assert)
    
    # Type keywords
    TEXT = auto()            # text (string type)
    DIGITS = auto()          # digits (number type)
    TF = auto()              # tf (boolean type)
    LINEUP = auto()          # lineup (array type)
    BAG = auto()             # bag (object/map type)
    VOID = auto()            # void
    CHOICES = auto()         # choices (enum type)
    
    # Literals
    REAL = auto()            # real (true)
    FAKE = auto()            # fake (false)
    GHOST = auto()           # ghost (null)
    STRING = auto()          # string literal
    NUMBER = auto()          # number literal
    
    # Operators
    PLUS = auto()            # +
    MINUS = auto()           # -
    STAR = auto()            # *
    SLASH = auto()           # /
    PERCENT = auto()         # %
    EQUAL_EQUAL = auto()     # ==
    BANG_EQUAL = auto()      # !=
    LESS = auto()            # <
    GREATER = auto()         # >
    LESS_EQUAL = auto()      # <=
    GREATER_EQUAL = auto()   # >=
    ARROW = auto()           # ->
    AND = auto()             # and
    OR = auto()              # or
    NOT = auto()             # not
    EQUAL = auto()           # =
    
    # Delimiters
    LEFT_PAREN = auto()      # (
    RIGHT_PAREN = auto()     # )
    LEFT_BRACE = auto()      # {
    RIGHT_BRACE = auto()     # }
    LEFT_BRACKET = auto()    # [
    RIGHT_BRACKET = auto()   # ]
    COMMA = auto()           # ,
    COLON = auto()           # :
    DOT = auto()             # .
    DOTDOT = auto()          # .. (range operator)
    SEMICOLON = auto()       # ;
    
    # Special
    IDENTIFIER = auto()      # variable/function names
    NEWLINE = auto()         # newline (statement separator)
    EOF = auto()             # end of file
    

@dataclass
class Position:
    """Source code position for error reporting."""
    filename: str
    line: int
    column: int
    
    def __str__(self) -> str:
        return f"{self.filename}:{self.line}:{self.column}"


@dataclass
class Token:
    """A lexical token."""
    type: TokenType
    lexeme: str
    literal: Any
    position: Position
    
    def __str__(self) -> str:
        if self.literal is not None:
            return f"{self.type.name}({self.lexeme}, {self.literal})"
        return f"{self.type.name}({self.lexeme})"
