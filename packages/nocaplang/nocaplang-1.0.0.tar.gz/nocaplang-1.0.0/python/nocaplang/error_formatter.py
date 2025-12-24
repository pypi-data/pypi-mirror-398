"""Enhanced error formatting for NoCapLang compiler.

This module provides utilities for formatting error messages with:
- Source code context/snippets
- Color coding for better readability
- File path and location information
- "Did you mean?" suggestions
"""

from typing import Optional, List
from .lexer.token import Position


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    GRAY = '\033[90m'


def format_error_with_context(
    message: str,
    position: Position,
    source: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    error_type: str = "Error",
    use_color: bool = True
) -> str:
    """Format an error message with source code context.
    
    Args:
        message: The error message
        position: Position of the error in source code
        source: Optional source code to extract context from
        suggestions: Optional list of suggestions (e.g., "did you mean?")
        error_type: Type of error (e.g., "Syntax Error", "Type Error")
        use_color: Whether to use ANSI color codes
        
    Returns:
        Formatted error message with context
    """
    lines = []
    
    # Error header with location
    if use_color:
        header = f"{Colors.BOLD}{Colors.RED}{error_type}{Colors.RESET}"
        location = f"{Colors.BOLD}{position.filename}:{position.line}:{position.column}{Colors.RESET}"
        lines.append(f"{header} at {location}")
    else:
        lines.append(f"{error_type} at {position.filename}:{position.line}:{position.column}")
    
    # Error message
    if use_color:
        lines.append(f"  {Colors.BOLD}{message}{Colors.RESET}")
    else:
        lines.append(f"  {message}")
    
    # Source code context
    if source:
        context = extract_source_context(source, position, use_color)
        if context:
            lines.append("")
            lines.extend(context)
    
    # Suggestions
    if suggestions:
        lines.append("")
        if use_color:
            lines.append(f"  {Colors.CYAN}Did you mean:{Colors.RESET}")
            for suggestion in suggestions:
                lines.append(f"    {Colors.GREEN}{suggestion}{Colors.RESET}")
        else:
            lines.append("  Did you mean:")
            for suggestion in suggestions:
                lines.append(f"    {suggestion}")
    
    return "\n".join(lines)


def extract_source_context(
    source: str,
    position: Position,
    use_color: bool = True,
    context_lines: int = 2
) -> List[str]:
    """Extract source code context around an error position.
    
    Args:
        source: The source code
        position: Position of the error
        use_color: Whether to use ANSI color codes
        context_lines: Number of lines to show before and after error line
        
    Returns:
        List of formatted context lines
    """
    lines = source.split('\n')
    error_line_idx = position.line - 1  # Convert to 0-based index
    
    if error_line_idx < 0 or error_line_idx >= len(lines):
        return []
    
    result = []
    
    # Calculate range of lines to show
    start_line = max(0, error_line_idx - context_lines)
    end_line = min(len(lines), error_line_idx + context_lines + 1)
    
    # Calculate width for line numbers
    max_line_num = end_line
    line_num_width = len(str(max_line_num))
    
    # Add context lines
    for i in range(start_line, end_line):
        line_num = i + 1
        line_content = lines[i]
        
        if i == error_line_idx:
            # This is the error line - highlight it
            if use_color:
                line_str = f"  {Colors.BOLD}{Colors.BLUE}{line_num:>{line_num_width}}{Colors.RESET} | {line_content}"
            else:
                line_str = f"  {line_num:>{line_num_width}} | {line_content}"
            result.append(line_str)
            
            # Add error indicator (caret)
            if position.column > 0:
                # Calculate spaces before caret
                spaces = " " * (line_num_width + 3 + position.column - 1)
                if use_color:
                    caret = f"{spaces}{Colors.BOLD}{Colors.RED}^{Colors.RESET}"
                else:
                    caret = f"{spaces}^"
                result.append(caret)
        else:
            # Context line
            if use_color:
                line_str = f"  {Colors.GRAY}{line_num:>{line_num_width}}{Colors.RESET} | {line_content}"
            else:
                line_str = f"  {line_num:>{line_num_width}} | {line_content}"
            result.append(line_str)
    
    return result


def format_lexer_error(error, source: Optional[str] = None, use_color: bool = True) -> str:
    """Format a lexer error with context.
    
    Args:
        error: LexerError instance
        source: Optional source code
        use_color: Whether to use color
        
    Returns:
        Formatted error message
    """
    return format_error_with_context(
        message=error.message,
        position=error.position,
        source=source,
        error_type="Lexical Error",
        use_color=use_color
    )


def format_parse_error(error, source: Optional[str] = None, use_color: bool = True) -> str:
    """Format a parse error with context.
    
    Args:
        error: ParseError instance
        source: Optional source code
        use_color: Whether to use color
        
    Returns:
        Formatted error message
    """
    return format_error_with_context(
        message=error.message,
        position=error.position,
        source=source,
        error_type="Syntax Error",
        use_color=use_color
    )


def format_semantic_error(error, source: Optional[str] = None, use_color: bool = True) -> str:
    """Format a semantic error with context.
    
    Args:
        error: SemanticError instance
        source: Optional source code
        use_color: Whether to use color
        
    Returns:
        Formatted error message
    """
    suggestions = getattr(error, 'suggestions', None)
    
    # Determine error type from message
    error_type = "Semantic Error"
    message_lower = error.message.lower()
    if 'type' in message_lower:
        error_type = "Type Error"
    elif 'undefined' in message_lower:
        error_type = "Name Error"
    
    return format_error_with_context(
        message=error.message,
        position=error.position,
        source=source,
        suggestions=suggestions,
        error_type=error_type,
        use_color=use_color
    )


def format_compilation_errors(
    errors: List,
    source: Optional[str] = None,
    use_color: bool = True
) -> str:
    """Format multiple compilation errors.
    
    Args:
        errors: List of error objects
        source: Optional source code
        use_color: Whether to use color
        
    Returns:
        Formatted error messages
    """
    if not errors:
        return ""
    
    formatted_errors = []
    
    for error in errors:
        # Determine error type and format accordingly
        error_class = error.__class__.__name__
        
        if 'Lexer' in error_class:
            formatted = format_lexer_error(error, source, use_color)
        elif 'Parse' in error_class:
            formatted = format_parse_error(error, source, use_color)
        elif 'Semantic' in error_class:
            formatted = format_semantic_error(error, source, use_color)
        else:
            # Generic error formatting
            if hasattr(error, 'position') and hasattr(error, 'message'):
                formatted = format_error_with_context(
                    message=error.message,
                    position=error.position,
                    source=source,
                    use_color=use_color
                )
            else:
                formatted = str(error)
        
        formatted_errors.append(formatted)
    
    # Add summary
    error_count = len(errors)
    if use_color:
        summary = f"\n{Colors.BOLD}{Colors.RED}Found {error_count} error{'s' if error_count != 1 else ''}{Colors.RESET}"
    else:
        summary = f"\nFound {error_count} error{'s' if error_count != 1 else ''}"
    
    return "\n\n".join(formatted_errors) + summary


def strip_colors(text: str) -> str:
    """Remove ANSI color codes from text.
    
    Args:
        text: Text with ANSI color codes
        
    Returns:
        Text without color codes
    """
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)
