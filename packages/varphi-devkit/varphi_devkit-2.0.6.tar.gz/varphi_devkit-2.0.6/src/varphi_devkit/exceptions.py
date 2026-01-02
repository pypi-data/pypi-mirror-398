from antlr4.error.ErrorListener import ErrorListener
from antlr4 import Token

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
BLUE = "\033[34m"
CYAN = "\033[96m"
WHITE = "\033[97m"


class VarphiSyntaxError(Exception):
    """
    Base exception class for all Varphi compilation errors.
    Captures context (line, column, symbol).
    """

    def __init__(self, recognizer, offendingSymbol, line, column, msg):
        self.recognizer = recognizer
        self.offendingSymbol = offendingSymbol
        self.line = line
        self.column = column
        self.msg = msg
        super().__init__(msg)

    def __str__(self) -> str:
        # Start the error message with a bold red "error:" label
        result = [f"\n{BOLD}{RED}error:{RESET} {BOLD}{WHITE}{self.msg}{RESET}"]
        result.append(f"{BLUE}   -->{RESET} line {self.line}:{self.column + 1}")

        # Attempt to retrieve the input stream to show the code snippet
        stream = None
        try:
            # Try getting the stream from the recognizer (parser/lexer)
            if self.recognizer:
                temp_stream = self.recognizer.getInputStream()
                if hasattr(temp_stream, "tokenSource"):
                    stream = temp_stream.tokenSource.inputStream
                else:
                    stream = temp_stream

            # If that fails, try getting it from the offending symbol (token)
            elif self.offendingSymbol:
                if hasattr(self.offendingSymbol, "getInputStream"):
                    stream = self.offendingSymbol.getInputStream()
                elif hasattr(self.offendingSymbol, "tokenSource"):
                    stream = self.offendingSymbol.tokenSource.inputStream

            # If we successfully found the stream, generate the code preview
            if stream:
                lines = str(stream).splitlines()
                # Ensure the line number is valid within the source
                if 0 <= self.line - 1 < len(lines):
                    code_line = lines[self.line - 1]

                    # Formatting constants for the "gutter"
                    gutter_width = 4
                    line_num_str = str(self.line)

                    # Print the empty pipe above the code line
                    result.append(f"{BLUE}{' ' * gutter_width} |{RESET}")

                    # Print the actual line of code with the line number
                    result.append(
                        f"{BLUE}{line_num_str:>{gutter_width}} |{RESET} {code_line}"
                    )

                    # Calculate the length of the error squiggle (^)
                    token_len = 1
                    if self.offendingSymbol and isinstance(self.offendingSymbol, Token):
                        start = self.offendingSymbol.start
                        stop = self.offendingSymbol.stop
                        if start is not None and stop is not None:
                            token_len = stop - start + 1

                    # Create the pointer line (e.g., "      |     ^~~~")
                    padding = " " * self.column
                    pointer = f"{BOLD}{RED}^{'~' * (token_len - 1)}{RESET}"
                    result.append(
                        f"{BLUE}{' ' * gutter_width} |{RESET} {padding}{pointer}"
                    )

        except Exception:
            # Fallback: If anything fails during error generation, just return the basic message
            pass

        return "\n".join(result)


class VarphiTransitionInconsistentTapeCountError(VarphiSyntaxError):
    """Raised when a single transition has mismatched read/write/shift tuple lengths."""

    def __init__(self, ctx, r_len, w_len, s_len):
        msg = (
            f"local tape count mismatch: read {r_len} symbols, "
            f"but wrote {w_len} and shifted {s_len}"
        )
        super().__init__(None, ctx.start, ctx.start.line, ctx.start.column, msg)


class VarphiGlobalTapeCountError(VarphiSyntaxError):
    """Raised when a transition's tape count doesn't match the machine's global tape count."""

    def __init__(self, ctx, expected, actual):
        msg = (
            f"global tape count mismatch: previous transitions used {expected} tapes, "
            f"but this one uses {actual}"
        )
        super().__init__(None, ctx.start, ctx.start.line, ctx.start.column, msg)


class VarphiUndefinedVariableError(VarphiSyntaxError):
    """Raised when a variable is used in a write tuple without being defined in the read tuple."""

    def __init__(self, ctx, variable_name):
        msg = (
            f"Undefined variable: '{variable_name}' is used in the write tuple "
            f"but was not defined in the read tuple."
        )
        super().__init__(None, ctx.start, ctx.start.line, ctx.start.column, msg)


class VarphiErrorListener(ErrorListener):
    """Custom ANTLR ErrorListener that converts syntax errors into VarphiSyntaxErrors."""

    def __init__(self):
        super().__init__()

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise VarphiSyntaxError(recognizer, offendingSymbol, line, column, msg)
