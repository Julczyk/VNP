# Generated from /home/julczyk/Dokumenty/Automaty/VNP/SRAPL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .SRAPLParser import SRAPLParser
else:
    from SRAPLParser import SRAPLParser

# This class defines a complete generic visitor for a parse tree produced by SRAPLParser.

class SRAPLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SRAPLParser#file.
    def visitFile(self, ctx:SRAPLParser.FileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#partsSection.
    def visitPartsSection(self, ctx:SRAPLParser.PartsSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#floatList.
    def visitFloatList(self, ctx:SRAPLParser.FloatListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#value.
    def visitValue(self, ctx:SRAPLParser.ValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#programmSection.
    def visitProgrammSection(self, ctx:SRAPLParser.ProgrammSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#blockContent.
    def visitBlockContent(self, ctx:SRAPLParser.BlockContentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#statement.
    def visitStatement(self, ctx:SRAPLParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#block.
    def visitBlock(self, ctx:SRAPLParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#assignment.
    def visitAssignment(self, ctx:SRAPLParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#functionCall.
    def visitFunctionCall(self, ctx:SRAPLParser.FunctionCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#argList.
    def visitArgList(self, ctx:SRAPLParser.ArgListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#ifStatement.
    def visitIfStatement(self, ctx:SRAPLParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#redoStatement.
    def visitRedoStatement(self, ctx:SRAPLParser.RedoStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#restartStatement.
    def visitRestartStatement(self, ctx:SRAPLParser.RestartStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#memoryRef.
    def visitMemoryRef(self, ctx:SRAPLParser.MemoryRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#variableExpr.
    def visitVariableExpr(self, ctx:SRAPLParser.VariableExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#powerExpr.
    def visitPowerExpr(self, ctx:SRAPLParser.PowerExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#addSubExpr.
    def visitAddSubExpr(self, ctx:SRAPLParser.AddSubExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#atomExpr.
    def visitAtomExpr(self, ctx:SRAPLParser.AtomExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#parensExpr.
    def visitParensExpr(self, ctx:SRAPLParser.ParensExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SRAPLParser#mulDivExpr.
    def visitMulDivExpr(self, ctx:SRAPLParser.MulDivExprContext):
        return self.visitChildren(ctx)



del SRAPLParser