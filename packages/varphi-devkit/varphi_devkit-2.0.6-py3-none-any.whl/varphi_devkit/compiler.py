from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker

from .parser import VarphiLexer
from .parser import VarphiParser
from .parser import VarphiListener

from .exceptions import (
    VarphiErrorListener,
    VarphiTransitionInconsistentTapeCountError,
    VarphiGlobalTapeCountError,
    VarphiUndefinedVariableError,
)

BLANK = "_"
LEFT = "LEFT"
RIGHT = "RIGHT"
STAY = "STAY"


@dataclass(frozen=True)
class VarphiTransition:
    """
    Represents a transition (a single line) in a Varphi program.
    Attributes:
        - current_state (str): String containing the name of the state the machine must be on to trigger this transition.
        - read_symbols (tuple[str, ...]): Tuple of strings containing the values the heads must read to trigger this transition. Strings starting with $ are variables and are guaranteed to be ordered ($1, $2, ...). Otherwise, members may be BLANK or alphanumericals.
        - next_state (str): The name of the next state to transition to when this transition is triggered.
        - write_symbols (tuple[str, ...]): Tuple of strings containing the values the heads will write when this transition is triggered. Follows the same format as read_symbols, and variable names appearing here are guaranteed to appear in read_symbols.
        - shift_directions (tuple[str, ...]): A tuple of strings containing the directions the heads will move in when this transition is triggered. Each element is guaranteed to be one of LEFT, RIGHT, or STAY
        - line_number (int): The line number in the source code this transition corresponds to.
    """

    current_state: str
    read_symbols: tuple[str, ...]
    next_state: str
    write_symbols: tuple[str, ...]
    shift_directions: tuple[str, ...]
    line_number: int


class VarphiCompiler(VarphiListener, ABC):
    """
    An abstract Varphi compiler.

    Concrete Varphi compiler implementations must subclass this class and implement the following methods:
        - handle_transition(self, transition: VarphiTransition) -> None: Automatically called at compile-time on each transition in the Varphi program
        - generate_compiled_program(self) -> str: Returns the compiled Varphi program after all transitions have been handled via handle_transition()
    If __init__() is overridden to add additional attributes (e.g., the compiled program so far), then
        - super().__init__() must be called
        - compile(self, program: str) -> str must be overridden to reset the state, followed by a call to super().__init__()
    """

    _expected_tape_count: Optional[int]

    def __init__(self):
        """Initialize this compiler."""
        self._expected_tape_count = None

    @abstractmethod
    def handle_transition(self, transition: VarphiTransition) -> None:
        """Handle a single transition in a Varphi program."""
        pass

    @abstractmethod
    def generate_compiled_program(self) -> str:
        """Generate the compiled program after all transitions have been handled."""
        pass

    def compile(self, program: str) -> str:
        """Compile a Varphi program."""
        # Reset state (subclasses must do so for their own state too)
        self._expected_tape_count = None

        input_stream = InputStream(program)
        error_listener = VarphiErrorListener()

        lexer = VarphiLexer(input_stream)
        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)

        token_stream = CommonTokenStream(lexer)
        parser = VarphiParser(token_stream)
        parser.removeErrorListeners()
        parser.addErrorListener(error_listener)

        tree = parser.program()
        walker = ParseTreeWalker()
        walker.walk(self, tree)

        return self.generate_compiled_program()

    def enterTransition(self, ctx: VarphiParser.TransitionContext) -> None:
        """Extract information from a raw transition context, and delegate to handle_transition()."""
        current_state = ctx.current_state.getText()
        next_state = ctx.next_state.getText()

        def extract_symbol(symbol_ctx) -> str:
            """Given a symbol context, extract the corresponding symbol string."""
            if symbol_ctx.VARIABLE():
                return symbol_ctx.VARIABLE().getText()
            if symbol_ctx.BLANK_KW():
                return BLANK
            if symbol_ctx.ALPHANUM():
                return symbol_ctx.ALPHANUM().getText()
            raise ValueError(f"Unknown symbol type: {symbol_ctx.getText()}")

        def extract_direction(symbol_ctx) -> str:
            """Given a direction context, extract the corresponding direction string."""
            if symbol_ctx.LEFT_KW():
                return LEFT
            if symbol_ctx.RIGHT_KW():
                return RIGHT
            if symbol_ctx.STAY_KW():
                return STAY
            raise ValueError(f"Unknown direction: {symbol_ctx.getText()}")

        read_ctx = ctx.read_symbols()
        reads = tuple(extract_symbol(s) for s in read_ctx.symbol()) if read_ctx else ()

        write_ctx = ctx.write_symbols()
        writes = (
            tuple(extract_symbol(s) for s in write_ctx.symbol()) if write_ctx else ()
        )

        shift_ctx = ctx.shift_directions()
        shifts = (
            tuple(extract_direction(d) for d in shift_ctx.direction())
            if shift_ctx
            else ()
        )

        # Check if the tuple-lengths of the transition are all the same
        if len(writes) != len(reads) or len(shifts) != len(reads):
            raise VarphiTransitionInconsistentTapeCountError(
                ctx, len(reads), len(writes), len(shifts)
            )

        # Use the tuple lengths of the first transition as ground truth and make sure all other transitions are consistent
        current_tape_count = len(reads)
        if self._expected_tape_count is None:
            self._expected_tape_count = current_tape_count
        elif current_tape_count != self._expected_tape_count:
            raise VarphiGlobalTapeCountError(
                ctx, self._expected_tape_count, current_tape_count
            )

        # Map user variables to $1, $2, $3... based on appearance in the read tuple
        # NOTE: This is just an optimization so that equivalent patterns ($x, $y) and ($y, $x) are easy call "equivalent"
        variable_map = {}
        next_var_id = 1
        canonical_reads = []
        for sym in reads:
            if sym.startswith("$"):
                # Check if we have already assigned an ID to this variable (e.g. read($x, $x))
                if sym not in variable_map:
                    variable_map[sym] = f"${next_var_id}"
                    next_var_id += 1
                canonical_reads.append(variable_map[sym])
            else:
                canonical_reads.append(sym)

        # Map write variables to their canonical versions
        canonical_writes = []
        for i, sym in enumerate(writes):
            if sym.startswith("$"):
                if sym not in variable_map:
                    # This variable is not defined in the read tuple
                    specific_ctx = write_ctx.symbol(i)
                    raise VarphiUndefinedVariableError(specific_ctx, sym)
                canonical_writes.append(variable_map[sym])
            else:
                canonical_writes.append(sym)

        transition = VarphiTransition(
            current_state=current_state,
            read_symbols=tuple(canonical_reads),
            next_state=next_state,
            write_symbols=tuple(canonical_writes),
            shift_directions=shifts,
            line_number=ctx.start.line,
        )
        self.handle_transition(transition)
