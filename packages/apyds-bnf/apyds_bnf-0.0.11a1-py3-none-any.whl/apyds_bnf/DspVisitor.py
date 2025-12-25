# Generated from /home/runner/work/_temp/setup-uv-cache/sdists-v9/.tmp8utGd6/apyds_bnf-0.0.11a1/Dsp.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .DspParser import DspParser
else:
    from DspParser import DspParser

# This class defines a complete generic visitor for a parse tree produced by DspParser.

class DspVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by DspParser#rule_pool.
    def visitRule_pool(self, ctx:DspParser.Rule_poolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DspParser#rule.
    def visitRule(self, ctx:DspParser.RuleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DspParser#symbol.
    def visitSymbol(self, ctx:DspParser.SymbolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DspParser#parentheses.
    def visitParentheses(self, ctx:DspParser.ParenthesesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DspParser#subscript.
    def visitSubscript(self, ctx:DspParser.SubscriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DspParser#binary.
    def visitBinary(self, ctx:DspParser.BinaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DspParser#function.
    def visitFunction(self, ctx:DspParser.FunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by DspParser#unary.
    def visitUnary(self, ctx:DspParser.UnaryContext):
        return self.visitChildren(ctx)



del DspParser