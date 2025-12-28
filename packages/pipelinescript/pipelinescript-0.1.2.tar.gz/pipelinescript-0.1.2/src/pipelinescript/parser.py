"""
Pipeline Parser - Lexical Analysis and Syntax Parsing
====================================================

Transforms human-readable PipelineScript into an Abstract Syntax Tree (AST).

Grammar:
    pipeline := statement+
    statement := command args*
    command := IDENTIFIER
    args := STRING | NUMBER | PATH | OPTION
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """Token types for lexical analysis."""
    COMMAND = "COMMAND"
    STRING = "STRING"
    NUMBER = "NUMBER"
    PATH = "PATH"
    OPTION = "OPTION"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


@dataclass
class Token:
    """Lexical token."""
    type: TokenType
    value: Any
    line: int
    column: int


@dataclass
class ASTNode:
    """Abstract Syntax Tree Node."""
    command: str
    args: List[Any]
    options: Dict[str, Any]
    line: int


class PipelineLexer:
    """Lexical analyzer for PipelineScript."""
    
    def __init__(self):
        self.tokens: List[Token] = []
        self.current = 0
        self.line = 1
        self.column = 1
    
    def tokenize(self, script: str) -> List[Token]:
        """
        Convert script into tokens.
        
        Args:
            script: PipelineScript source code
            
        Returns:
            List of tokens
        """
        self.tokens = []
        self.current = 0
        self.line = 1
        self.column = 1
        
        lines = script.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Tokenize line
            self._tokenize_line(line, line_num)
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        
        return self.tokens
    
    def _tokenize_line(self, line: str, line_num: int):
        """Tokenize a single line."""
        parts = self._split_line(line)
        
        if not parts:
            return
        
        # First part is always a command
        self.tokens.append(Token(
            TokenType.COMMAND,
            parts[0].lower(),
            line_num,
            1
        ))
        
        # Parse arguments
        for i, part in enumerate(parts[1:], 1):
            token = self._parse_token(part, line_num, i)
            if token:
                self.tokens.append(token)
    
    def _split_line(self, line: str) -> List[str]:
        """Split line into parts, respecting quotes."""
        parts = []
        current = []
        in_quotes = False
        quote_char = None
        
        for char in line:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char.isspace() and not in_quotes:
                if current:
                    parts.append(''.join(current))
                    current = []
                continue
            
            current.append(char)
        
        if current:
            parts.append(''.join(current))
        
        return parts
    
    def _parse_token(self, text: str, line: int, col: int) -> Optional[Token]:
        """Parse a single token."""
        # Option (--flag or -f)
        if text.startswith('--') or (text.startswith('-') and len(text) == 2):
            return Token(TokenType.OPTION, text, line, col)
        
        # Number
        if re.match(r'^-?\d+\.?\d*$', text):
            value = float(text) if '.' in text else int(text)
            return Token(TokenType.NUMBER, value, line, col)
        
        # Path (contains / or \ or has file extension)
        if '/' in text or '\\' in text or '.' in text:
            return Token(TokenType.PATH, text, line, col)
        
        # String (remove quotes if present)
        if text.startswith(('"', "'")) and text.endswith(('"', "'")):
            return Token(TokenType.STRING, text[1:-1], line, col)
        
        # Default to string
        return Token(TokenType.STRING, text, line, col)


class PipelineParser:
    """Parser for PipelineScript."""
    
    def __init__(self):
        self.lexer = PipelineLexer()
        self.tokens: List[Token] = []
        self.current = 0
    
    def parse(self, script: str) -> List[ASTNode]:
        """
        Parse PipelineScript into AST.
        
        Args:
            script: PipelineScript source code
            
        Returns:
            List of AST nodes representing the pipeline
            
        Example:
            >>> parser = PipelineParser()
            >>> ast = parser.parse("load data.csv\\ntrain xgboost")
            >>> len(ast)
            2
        """
        self.tokens = self.lexer.tokenize(script)
        self.current = 0
        
        ast = []
        
        while not self._is_at_end():
            node = self._parse_statement()
            if node:
                ast.append(node)
        
        return ast
    
    def _parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        if self._is_at_end():
            return None
        
        # Get command
        command_token = self._advance()
        
        if command_token.type != TokenType.COMMAND:
            raise SyntaxError(
                f"Expected command at line {command_token.line}, "
                f"got {command_token.type.value}"
            )
        
        args = []
        options = {}
        
        # Parse arguments and options
        while not self._is_at_end() and self._peek().type != TokenType.COMMAND:
            token = self._advance()
            
            if token.type == TokenType.EOF:
                break
            
            if token.type == TokenType.OPTION:
                # Parse option
                option_name = token.value.lstrip('-')
                
                # Check if option has a value
                if not self._is_at_end() and self._peek().type != TokenType.OPTION:
                    next_token = self._peek()
                    if next_token.type != TokenType.COMMAND:
                        value_token = self._advance()
                        options[option_name] = value_token.value
                    else:
                        options[option_name] = True
                else:
                    options[option_name] = True
            else:
                args.append(token.value)
        
        return ASTNode(
            command=command_token.value,
            args=args,
            options=options,
            line=command_token.line
        )
    
    def _advance(self) -> Token:
        """Consume and return current token."""
        if not self._is_at_end():
            self.current += 1
        return self.tokens[self.current - 1]
    
    def _peek(self) -> Token:
        """Return current token without consuming."""
        return self.tokens[self.current]
    
    def _is_at_end(self) -> bool:
        """Check if at end of tokens."""
        return self.current >= len(self.tokens) or self._peek().type == TokenType.EOF


def parse_pipeline(script: str) -> List[ASTNode]:
    """Convenience function to parse a pipeline script."""
    parser = PipelineParser()
    return parser.parse(script)
