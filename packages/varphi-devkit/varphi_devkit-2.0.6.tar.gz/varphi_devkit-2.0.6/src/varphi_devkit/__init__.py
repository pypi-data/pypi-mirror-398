"""
The Varphi Development Kit.

A framework for building compilers, interpreters, and analysis tools for the Varphi language.
This package handles the complexity of parsing, validation, and variable canonicalization, providing a
convenient abstraction layer for implementing custom Varphi backends.

**Core API:**
- `VarphiCompiler`: The abstract base class you must subclass. Override `handle_transition` to process logic.
- `VarphiTransition`: A validated, canonicalized representation of a single transition line.

**Constants:**
- `BLANK`, `LEFT`, `RIGHT`, `STAY`: Primitives for tape operations.

**Exceptions:**
- `VarphiSyntaxError`: Base class for rich error reporting with source code context.
"""

from .compiler import VarphiCompiler, VarphiTransition, BLANK, LEFT, RIGHT, STAY
from .exceptions import (
    VarphiSyntaxError,
    VarphiTransitionInconsistentTapeCountError,
    VarphiGlobalTapeCountError,
    VarphiUndefinedVariableError,
)

__all__ = [
    "VarphiCompiler",
    "VarphiTransition",
    "BLANK",
    "LEFT",
    "RIGHT",
    "STAY",
    "VarphiSyntaxError",
    "VarphiTransitionInconsistentTapeCountError",
    "VarphiGlobalTapeCountError",
    "VarphiUndefinedVariableError",
]
