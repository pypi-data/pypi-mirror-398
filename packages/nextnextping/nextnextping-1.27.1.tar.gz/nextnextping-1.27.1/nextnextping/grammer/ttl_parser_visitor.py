# Generated from TtlParser.g4 by ANTLR 4.13.2
from antlr4 import ParseTreeVisitor

if "." in __name__:
    from .TtlParserParser import TtlParserParser
else:
    from TtlParserParser import TtlParserParser

# This class defines a complete generic visitor for a parse tree produced by TtlParserParser.


class TtlParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by TtlParserParser#strContext.
    def visitStrContext(self, ctx: TtlParserParser.StrContextContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#keyword.
    def visitKeyword(self, ctx: TtlParserParser.KeywordContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#strExpression.
    def visitStrExpression(self, ctx: TtlParserParser.StrExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#intContext.
    def visitIntContext(self, ctx: TtlParserParser.IntContextContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#intExpression.
    def visitIntExpression(self, ctx: TtlParserParser.IntExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p1Expression.
    def visitP1Expression(self, ctx: TtlParserParser.P1ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p2Expression.
    def visitP2Expression(self, ctx: TtlParserParser.P2ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p3Expression.
    def visitP3Expression(self, ctx: TtlParserParser.P3ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p4Expression.
    def visitP4Expression(self, ctx: TtlParserParser.P4ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p5Expression.
    def visitP5Expression(self, ctx: TtlParserParser.P5ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p6Expression.
    def visitP6Expression(self, ctx: TtlParserParser.P6ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p7Expression.
    def visitP7Expression(self, ctx: TtlParserParser.P7ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p8Expression.
    def visitP8Expression(self, ctx: TtlParserParser.P8ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p9Expression.
    def visitP9Expression(self, ctx: TtlParserParser.P9ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p10Expression.
    def visitP10Expression(self, ctx: TtlParserParser.P10ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#p11Expression.
    def visitP11Expression(self, ctx: TtlParserParser.P11ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#command.
    def visitCommand(self, ctx: TtlParserParser.CommandContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#forNext.
    def visitForNext(self, ctx: TtlParserParser.ForNextContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#whileEndwhile.
    def visitWhileEndwhile(self, ctx: TtlParserParser.WhileEndwhileContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#untilEnduntil.
    def visitUntilEnduntil(self, ctx: TtlParserParser.UntilEnduntilContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#doLoop.
    def visitDoLoop(self, ctx: TtlParserParser.DoLoopContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#if1.
    def visitIf1(self, ctx: TtlParserParser.If1Context):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#if2.
    def visitIf2(self, ctx: TtlParserParser.If2Context):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#elseif.
    def visitElseif(self, ctx: TtlParserParser.ElseifContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#else.
    def visitElse(self, ctx: TtlParserParser.ElseContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#input.
    def visitInput(self, ctx: TtlParserParser.InputContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#label.
    def visitLabel(self, ctx: TtlParserParser.LabelContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#commandline.
    def visitCommandline(self, ctx: TtlParserParser.CommandlineContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by TtlParserParser#statement.
    def visitStatement(self, ctx: TtlParserParser.StatementContext):
        return self.visitChildren(ctx)


del TtlParserParser
