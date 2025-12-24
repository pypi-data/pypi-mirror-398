"""Lexer (tokenizer) for NoCapLang."""

from typing import List, Optional
from .token import Token, TokenType, Position


class LexerError(Exception):
    """Exception raised for lexical errors."""
    
    def __init__(self, message: str, position: Position):
        self.message = message
        self.position = position
        super().__init__(f"{position}: {message}")


class Lexer:
    """Lexical analyzer for NoCapLang source code."""
    
    # Keyword mapping
    KEYWORDS = {
        'fr': TokenType.FR,
        'yap': TokenType.YAP,
        'vibecheck': TokenType.VIBECHECK,
        'nah': TokenType.NAH,
        'run': TokenType.RUN,
        'until': TokenType.UNTIL,
        'each': TokenType.EACH,
        'lowkey': TokenType.LOWKEY,
        'comeback': TokenType.COMEBACK,
        'dip': TokenType.DIP,
        'skip': TokenType.SKIP,
        'tryna': TokenType.TRYNA,
        'oops': TokenType.OOPS,
        'nomatter': TokenType.NOMATTER,
        'crash': TokenType.CRASH,
        'vibe': TokenType.VIBE,
        'vibes_with': TokenType.VIBES_WITH,
        'self': TokenType.SELF,
        'chill': TokenType.CHILL,
        'holdup': TokenType.HOLDUP,
        'match': TokenType.MATCH,
        'check': TokenType.CHECK,
        'case': TokenType.CASE,
        'hits': TokenType.HITS,
        'otherwise': TokenType.OTHERWISE,
        'grab': TokenType.GRAB,
        'nocap': TokenType.NOCAP,
        'text': TokenType.TEXT,
        'digits': TokenType.DIGITS,
        'tf': TokenType.TF,
        'lineup': TokenType.LINEUP,
        'bag': TokenType.BAG,
        'void': TokenType.VOID,
        'choices': TokenType.CHOICES,
        'real': TokenType.REAL,
        'fake': TokenType.FAKE,
        'ghost': TokenType.GHOST,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
    }
    
    def __init__(self, source: str, filename: str = "<input>"):
        """Initialize the lexer.
        
        Args:
            source: Source code to tokenize
            filename: Name of the source file (for error reporting)
        """
        self.source = source
        self.filename = filename
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.line_start = 0  # Track start of current line for column calculation
    
    def scan_tokens(self) -> List[Token]:
        """Scan all tokens from the source code.
        
        Returns:
            List of tokens
            
        Raises:
            LexerError: If invalid characters or unterminated strings are encountered
        """
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()
        
        # Add EOF token
        self.tokens.append(Token(
            TokenType.EOF,
            "",
            None,
            Position(self.filename, self.line, self.column)
        ))
        
        return self.tokens
    
    def _scan_token(self) -> None:
        """Scan a single token."""
        # Save starting position for this token
        self.token_start_line = self.line
        self.token_start_column = self.column
        
        c = self._advance()
        
        # Single-character tokens
        if c == '(':
            self._add_token(TokenType.LEFT_PAREN)
        elif c == ')':
            self._add_token(TokenType.RIGHT_PAREN)
        elif c == '{':
            self._add_token(TokenType.LEFT_BRACE)
        elif c == '}':
            self._add_token(TokenType.RIGHT_BRACE)
        elif c == '[':
            self._add_token(TokenType.LEFT_BRACKET)
        elif c == ']':
            self._add_token(TokenType.RIGHT_BRACKET)
        elif c == ',':
            self._add_token(TokenType.COMMA)
        elif c == '.':
            # Check for .. (range operator)
            if self._peek() == '.':
                self._advance()  # consume second '.'
                self._add_token(TokenType.DOTDOT)
            else:
                self._add_token(TokenType.DOT)
        elif c == ';':
            self._add_token(TokenType.SEMICOLON)
        elif c == '+':
            self._add_token(TokenType.PLUS)
        elif c == '-':
            if self._match('>'):
                self._add_token(TokenType.ARROW)
            else:
                self._add_token(TokenType.MINUS)
        elif c == '*':
            self._add_token(TokenType.STAR)
        elif c == '/':
            self._add_token(TokenType.SLASH)
        elif c == '%':
            self._add_token(TokenType.PERCENT)
        
        # Two-character tokens
        elif c == '=':
            if self._match('='):
                self._add_token(TokenType.EQUAL_EQUAL)
            else:
                self._add_token(TokenType.EQUAL)
        elif c == '!':
            if self._match('='):
                self._add_token(TokenType.BANG_EQUAL)
            else:
                self._error(f"Unexpected character '!'")
        elif c == '<':
            if self._match('='):
                self._add_token(TokenType.LESS_EQUAL)
            else:
                self._add_token(TokenType.LESS)
        elif c == '>':
            if self._match('='):
                self._add_token(TokenType.GREATER_EQUAL)
            else:
                self._add_token(TokenType.GREATER)
        elif c == ':':
            # Check for :end (end of multi-line comment)
            if self._peek() == 'e' and self._peek_ahead(1) == 'n' and self._peek_ahead(2) == 'd':
                # This is handled in the rant: comment scanner
                self._add_token(TokenType.COLON)
            else:
                self._add_token(TokenType.COLON)
        
        # Whitespace (except newline)
        elif c in ' \r\t':
            pass  # Ignore whitespace
        
        # Newline
        elif c == '\n':
            self._add_token(TokenType.NEWLINE)
            self.line += 1
            self.line_start = self.current
            self.column = 1
        
        # String literals
        elif c == '"':
            self._string()
        
        # Numbers
        elif c.isdigit():
            self._number()
        
        # Identifiers and keywords
        elif c.isalpha() or c == '_':
            self._identifier()
        
        else:
            self._error(f"Unexpected character '{c}'")
    
    def _identifier(self) -> None:
        """Scan an identifier or keyword."""
        # Continue while alphanumeric or underscore (Unicode support)
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()
        
        text = self.source[self.start:self.current]
        
        # Check for special comment keywords
        if text == 'tea' and self._peek() == ':':
            self._advance()  # consume ':'
            self._single_line_comment()
            return
        elif text == 'rant' and self._peek() == ':':
            self._advance()  # consume ':'
            self._multi_line_comment()
            return
        
        # Check if it's a keyword
        token_type = self.KEYWORDS.get(text, TokenType.IDENTIFIER)
        
        # For boolean and null literals, store the actual value
        if token_type == TokenType.REAL:
            self._add_token(token_type, True)
        elif token_type == TokenType.FAKE:
            self._add_token(token_type, False)
        elif token_type == TokenType.GHOST:
            self._add_token(token_type, None)
        else:
            self._add_token(token_type)
    
    def _number(self) -> None:
        """Scan a number literal (integer or float)."""
        # Consume digits
        while self._peek().isdigit():
            self._advance()
        
        # Look for decimal point
        if self._peek() == '.' and self._peek_ahead(1).isdigit():
            # Consume the '.'
            self._advance()
            
            # Consume fractional digits
            while self._peek().isdigit():
                self._advance()
        
        # Check for scientific notation
        peek_char = self._peek()
        if peek_char and peek_char in 'eE':
            self._advance()
            
            # Optional sign
            peek_char = self._peek()
            if peek_char and peek_char in '+-':
                self._advance()
            
            # Exponent digits
            peek_char = self._peek()
            if not peek_char or not peek_char.isdigit():
                self._error("Invalid number format: expected digits after exponent")
                return
            
            while self._peek() and self._peek().isdigit():
                self._advance()
        
        text = self.source[self.start:self.current]
        try:
            value = float(text)
            self._add_token(TokenType.NUMBER, value)
        except ValueError:
            self._error(f"Invalid number format: {text}")
    
    def _string(self) -> None:
        """Scan a string literal with escape sequences."""
        value = []
        
        while not self._is_at_end() and self._peek() != '"':
            # Handle escape sequences
            if self._peek() == '\\':
                self._advance()  # consume '\'
                
                if self._is_at_end():
                    self._error("Unterminated string")
                    return
                
                escape_char = self._advance()
                
                if escape_char == 'n':
                    value.append('\n')
                elif escape_char == 't':
                    value.append('\t')
                elif escape_char == 'r':
                    value.append('\r')
                elif escape_char == '"':
                    value.append('"')
                elif escape_char == '\\':
                    value.append('\\')
                else:
                    # Unknown escape sequence - just include the character
                    value.append(escape_char)
            else:
                char = self._advance()
                value.append(char)
                
                # Track newlines for position tracking
                if char == '\n':
                    self.line += 1
                    self.line_start = self.current
                    self.column = 1
        
        if self._is_at_end():
            self._error("Unterminated string")
            return
        
        # Consume closing "
        self._advance()
        
        self._add_token(TokenType.STRING, ''.join(value))
    
    def _single_line_comment(self) -> None:
        """Skip a single-line comment (tea:)."""
        # Consume until end of line or end of file
        while not self._is_at_end() and self._peek() != '\n':
            self._advance()
    
    def _multi_line_comment(self) -> None:
        """Skip a multi-line comment (rant: ... :end)."""
        # Look for :end
        while not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
                self.line_start = self.current + 1
                self.column = 1
                self._advance()
            elif self._peek() == ':':
                # Check if this is :end
                if (self._peek_ahead(1) == 'e' and 
                    self._peek_ahead(2) == 'n' and 
                    self._peek_ahead(3) == 'd'):
                    # Consume :end
                    self._advance()  # :
                    self._advance()  # e
                    self._advance()  # n
                    self._advance()  # d
                    return
                else:
                    self._advance()
            else:
                self._advance()
        
        # If we reach here, the comment was not terminated
        self._error("Unterminated multi-line comment (missing :end)")
    
    def _match(self, expected: str) -> bool:
        """Check if current character matches expected and consume it.
        
        Args:
            expected: Character to match
            
        Returns:
            True if matched and consumed, False otherwise
        """
        if self._is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        
        self.current += 1
        self.column += 1
        return True
    
    def _peek(self) -> str:
        """Look at current character without consuming it.
        
        Returns:
            Current character or empty string if at end
        """
        if self._is_at_end():
            return ''
        return self.source[self.current]
    
    def _peek_ahead(self, n: int) -> str:
        """Look ahead n characters without consuming.
        
        Args:
            n: Number of characters to look ahead
            
        Returns:
            Character at position current+n or empty string if out of bounds
        """
        pos = self.current + n
        if pos >= len(self.source):
            return ''
        return self.source[pos]
    
    def _advance(self) -> str:
        """Consume and return current character.
        
        Returns:
            Current character
        """
        if self._is_at_end():
            return ''
        c = self.source[self.current]
        self.current += 1
        self.column += 1
        return c
    
    def _is_at_end(self) -> bool:
        """Check if we've reached the end of source.
        
        Returns:
            True if at end, False otherwise
        """
        return self.current >= len(self.source)
    
    def _add_token(self, token_type: TokenType, literal: any = None) -> None:
        """Add a token to the token list.
        
        Args:
            token_type: Type of the token
            literal: Literal value (for strings, numbers, booleans, null)
        """
        text = self.source[self.start:self.current]
        position = Position(
            self.filename,
            self.token_start_line,
            self.token_start_column
        )
        self.tokens.append(Token(token_type, text, literal, position))
    
    def _error(self, message: str) -> None:
        """Raise a lexer error.
        
        Args:
            message: Error message
            
        Raises:
            LexerError
        """
        position = Position(
            self.filename,
            self.line,
            self.start - self.line_start + 1
        )
        raise LexerError(message, position)
