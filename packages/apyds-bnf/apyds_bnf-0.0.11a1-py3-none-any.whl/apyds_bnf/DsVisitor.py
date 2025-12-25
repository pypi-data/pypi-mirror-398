# Generated from /home/runner/work/_temp/setup-uv-cache/sdists-v9/.tmp8utGd6/apyds_bnf-0.0.11a1/Ds.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .DsParser import DsParser
else:
    from DsParser import DsParser

# This class defines a complete generic visitor for a parse tree produced by DsParser.

class DsVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by DsParser#rule_pool.
    def visitRule_pool(self, ctx:DsParser.Rule_poolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DsParser#rule.
    def visitRule(self, ctx:DsParser.RuleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DsParser#symbol.
    def visitSymbol(self, ctx:DsParser.SymbolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DsParser#subscript.
    def visitSubscript(self, ctx:DsParser.SubscriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DsParser#function.
    def visitFunction(self, ctx:DsParser.FunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DsParser#unary.
    def visitUnary(self, ctx:DsParser.UnaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DsParser#binary.
    def visitBinary(self, ctx:DsParser.BinaryContext):
        return self.visitChildren(ctx)



del DsParser