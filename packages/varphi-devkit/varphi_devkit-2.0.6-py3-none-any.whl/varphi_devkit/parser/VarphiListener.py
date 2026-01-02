# Generated from Varphi.g4 by ANTLR 4.13.2
from antlr4 import *

if "." in __name__:
    from .VarphiParser import VarphiParser
else:
    from VarphiParser import VarphiParser


# This class defines a complete listener for a parse tree produced by VarphiParser.
class VarphiListener(ParseTreeListener):

    # Enter a parse tree produced by VarphiParser#program.
    def enterProgram(self, ctx: VarphiParser.ProgramContext):
        pass

    # Exit a parse tree produced by VarphiParser#program.
    def exitProgram(self, ctx: VarphiParser.ProgramContext):
        pass

    # Enter a parse tree produced by VarphiParser#transition.
    def enterTransition(self, ctx: VarphiParser.TransitionContext):
        pass

    # Exit a parse tree produced by VarphiParser#transition.
    def exitTransition(self, ctx: VarphiParser.TransitionContext):
        pass

    # Enter a parse tree produced by VarphiParser#read_symbols.
    def enterRead_symbols(self, ctx: VarphiParser.Read_symbolsContext):
        pass

    # Exit a parse tree produced by VarphiParser#read_symbols.
    def exitRead_symbols(self, ctx: VarphiParser.Read_symbolsContext):
        pass

    # Enter a parse tree produced by VarphiParser#write_symbols.
    def enterWrite_symbols(self, ctx: VarphiParser.Write_symbolsContext):
        pass

    # Exit a parse tree produced by VarphiParser#write_symbols.
    def exitWrite_symbols(self, ctx: VarphiParser.Write_symbolsContext):
        pass

    # Enter a parse tree produced by VarphiParser#shift_directions.
    def enterShift_directions(self, ctx: VarphiParser.Shift_directionsContext):
        pass

    # Exit a parse tree produced by VarphiParser#shift_directions.
    def exitShift_directions(self, ctx: VarphiParser.Shift_directionsContext):
        pass

    # Enter a parse tree produced by VarphiParser#state_id.
    def enterState_id(self, ctx: VarphiParser.State_idContext):
        pass

    # Exit a parse tree produced by VarphiParser#state_id.
    def exitState_id(self, ctx: VarphiParser.State_idContext):
        pass

    # Enter a parse tree produced by VarphiParser#symbol.
    def enterSymbol(self, ctx: VarphiParser.SymbolContext):
        pass

    # Exit a parse tree produced by VarphiParser#symbol.
    def exitSymbol(self, ctx: VarphiParser.SymbolContext):
        pass

    # Enter a parse tree produced by VarphiParser#direction.
    def enterDirection(self, ctx: VarphiParser.DirectionContext):
        pass

    # Exit a parse tree produced by VarphiParser#direction.
    def exitDirection(self, ctx: VarphiParser.DirectionContext):
        pass


del VarphiParser
