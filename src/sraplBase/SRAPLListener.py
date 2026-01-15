# Generated from /home/julczyk/Dokumenty/Automaty/VNP/SRAPL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .SRAPLParser import SRAPLParser
else:
    from SRAPLParser import SRAPLParser

# This class defines a complete listener for a parse tree produced by SRAPLParser.
class SRAPLListener(ParseTreeListener):

    # Enter a parse tree produced by SRAPLParser#file.
    def enterFile(self, ctx:SRAPLParser.FileContext):
        pass

    # Exit a parse tree produced by SRAPLParser#file.
    def exitFile(self, ctx:SRAPLParser.FileContext):
        pass


    # Enter a parse tree produced by SRAPLParser#partsSection.
    def enterPartsSection(self, ctx:SRAPLParser.PartsSectionContext):
        pass

    # Exit a parse tree produced by SRAPLParser#partsSection.
    def exitPartsSection(self, ctx:SRAPLParser.PartsSectionContext):
        pass


    # Enter a parse tree produced by SRAPLParser#floatList.
    def enterFloatList(self, ctx:SRAPLParser.FloatListContext):
        pass

    # Exit a parse tree produced by SRAPLParser#floatList.
    def exitFloatList(self, ctx:SRAPLParser.FloatListContext):
        pass


    # Enter a parse tree produced by SRAPLParser#value.
    def enterValue(self, ctx:SRAPLParser.ValueContext):
        pass

    # Exit a parse tree produced by SRAPLParser#value.
    def exitValue(self, ctx:SRAPLParser.ValueContext):
        pass


    # Enter a parse tree produced by SRAPLParser#programmSection.
    def enterProgrammSection(self, ctx:SRAPLParser.ProgrammSectionContext):
        pass

    # Exit a parse tree produced by SRAPLParser#programmSection.
    def exitProgrammSection(self, ctx:SRAPLParser.ProgrammSectionContext):
        pass


    # Enter a parse tree produced by SRAPLParser#blockContent.
    def enterBlockContent(self, ctx:SRAPLParser.BlockContentContext):
        pass

    # Exit a parse tree produced by SRAPLParser#blockContent.
    def exitBlockContent(self, ctx:SRAPLParser.BlockContentContext):
        pass


    # Enter a parse tree produced by SRAPLParser#statement.
    def enterStatement(self, ctx:SRAPLParser.StatementContext):
        pass

    # Exit a parse tree produced by SRAPLParser#statement.
    def exitStatement(self, ctx:SRAPLParser.StatementContext):
        pass


    # Enter a parse tree produced by SRAPLParser#block.
    def enterBlock(self, ctx:SRAPLParser.BlockContext):
        pass

    # Exit a parse tree produced by SRAPLParser#block.
    def exitBlock(self, ctx:SRAPLParser.BlockContext):
        pass


    # Enter a parse tree produced by SRAPLParser#assignment.
    def enterAssignment(self, ctx:SRAPLParser.AssignmentContext):
        pass

    # Exit a parse tree produced by SRAPLParser#assignment.
    def exitAssignment(self, ctx:SRAPLParser.AssignmentContext):
        pass


    # Enter a parse tree produced by SRAPLParser#functionCall.
    def enterFunctionCall(self, ctx:SRAPLParser.FunctionCallContext):
        pass

    # Exit a parse tree produced by SRAPLParser#functionCall.
    def exitFunctionCall(self, ctx:SRAPLParser.FunctionCallContext):
        pass


    # Enter a parse tree produced by SRAPLParser#argList.
    def enterArgList(self, ctx:SRAPLParser.ArgListContext):
        pass

    # Exit a parse tree produced by SRAPLParser#argList.
    def exitArgList(self, ctx:SRAPLParser.ArgListContext):
        pass


    # Enter a parse tree produced by SRAPLParser#ifStatement.
    def enterIfStatement(self, ctx:SRAPLParser.IfStatementContext):
        pass

    # Exit a parse tree produced by SRAPLParser#ifStatement.
    def exitIfStatement(self, ctx:SRAPLParser.IfStatementContext):
        pass


    # Enter a parse tree produced by SRAPLParser#redoStatement.
    def enterRedoStatement(self, ctx:SRAPLParser.RedoStatementContext):
        pass

    # Exit a parse tree produced by SRAPLParser#redoStatement.
    def exitRedoStatement(self, ctx:SRAPLParser.RedoStatementContext):
        pass


    # Enter a parse tree produced by SRAPLParser#restartStatement.
    def enterRestartStatement(self, ctx:SRAPLParser.RestartStatementContext):
        pass

    # Exit a parse tree produced by SRAPLParser#restartStatement.
    def exitRestartStatement(self, ctx:SRAPLParser.RestartStatementContext):
        pass


    # Enter a parse tree produced by SRAPLParser#memoryRef.
    def enterMemoryRef(self, ctx:SRAPLParser.MemoryRefContext):
        pass

    # Exit a parse tree produced by SRAPLParser#memoryRef.
    def exitMemoryRef(self, ctx:SRAPLParser.MemoryRefContext):
        pass


    # Enter a parse tree produced by SRAPLParser#variableExpr.
    def enterVariableExpr(self, ctx:SRAPLParser.VariableExprContext):
        pass

    # Exit a parse tree produced by SRAPLParser#variableExpr.
    def exitVariableExpr(self, ctx:SRAPLParser.VariableExprContext):
        pass


    # Enter a parse tree produced by SRAPLParser#powerExpr.
    def enterPowerExpr(self, ctx:SRAPLParser.PowerExprContext):
        pass

    # Exit a parse tree produced by SRAPLParser#powerExpr.
    def exitPowerExpr(self, ctx:SRAPLParser.PowerExprContext):
        pass


    # Enter a parse tree produced by SRAPLParser#addSubExpr.
    def enterAddSubExpr(self, ctx:SRAPLParser.AddSubExprContext):
        pass

    # Exit a parse tree produced by SRAPLParser#addSubExpr.
    def exitAddSubExpr(self, ctx:SRAPLParser.AddSubExprContext):
        pass


    # Enter a parse tree produced by SRAPLParser#atomExpr.
    def enterAtomExpr(self, ctx:SRAPLParser.AtomExprContext):
        pass

    # Exit a parse tree produced by SRAPLParser#atomExpr.
    def exitAtomExpr(self, ctx:SRAPLParser.AtomExprContext):
        pass


    # Enter a parse tree produced by SRAPLParser#parensExpr.
    def enterParensExpr(self, ctx:SRAPLParser.ParensExprContext):
        pass

    # Exit a parse tree produced by SRAPLParser#parensExpr.
    def exitParensExpr(self, ctx:SRAPLParser.ParensExprContext):
        pass


    # Enter a parse tree produced by SRAPLParser#mulDivExpr.
    def enterMulDivExpr(self, ctx:SRAPLParser.MulDivExprContext):
        pass

    # Exit a parse tree produced by SRAPLParser#mulDivExpr.
    def exitMulDivExpr(self, ctx:SRAPLParser.MulDivExprContext):
        pass



del SRAPLParser