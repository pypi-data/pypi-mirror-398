# Generated from /home/runner/work/_temp/setup-uv-cache/sdists-v9/.tmp8utGd6/apyds_bnf-0.0.11a1/Ds.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,10,80,2,0,7,0,2,1,7,1,2,2,7,2,1,0,5,0,8,8,0,10,0,12,0,11,9,0,
        1,0,1,0,4,0,15,8,0,11,0,12,0,16,1,0,5,0,20,8,0,10,0,12,0,23,9,0,
        3,0,25,8,0,1,0,5,0,28,8,0,10,0,12,0,31,9,0,1,0,1,0,1,1,1,1,4,1,37,
        8,1,11,1,12,1,38,5,1,41,8,1,10,1,12,1,44,9,1,1,1,1,1,1,1,1,1,1,2,
        1,2,1,2,5,2,53,8,2,10,2,12,2,56,9,2,1,2,1,2,1,2,5,2,61,8,2,10,2,
        12,2,64,9,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,3,2,
        78,8,2,1,2,0,0,3,0,2,4,0,0,89,0,9,1,0,0,0,2,42,1,0,0,0,4,77,1,0,
        0,0,6,8,5,9,0,0,7,6,1,0,0,0,8,11,1,0,0,0,9,7,1,0,0,0,9,10,1,0,0,
        0,10,24,1,0,0,0,11,9,1,0,0,0,12,21,3,2,1,0,13,15,5,9,0,0,14,13,1,
        0,0,0,15,16,1,0,0,0,16,14,1,0,0,0,16,17,1,0,0,0,17,18,1,0,0,0,18,
        20,3,2,1,0,19,14,1,0,0,0,20,23,1,0,0,0,21,19,1,0,0,0,21,22,1,0,0,
        0,22,25,1,0,0,0,23,21,1,0,0,0,24,12,1,0,0,0,24,25,1,0,0,0,25,29,
        1,0,0,0,26,28,5,9,0,0,27,26,1,0,0,0,28,31,1,0,0,0,29,27,1,0,0,0,
        29,30,1,0,0,0,30,32,1,0,0,0,31,29,1,0,0,0,32,33,5,0,0,1,33,1,1,0,
        0,0,34,36,3,4,2,0,35,37,5,9,0,0,36,35,1,0,0,0,37,38,1,0,0,0,38,36,
        1,0,0,0,38,39,1,0,0,0,39,41,1,0,0,0,40,34,1,0,0,0,41,44,1,0,0,0,
        42,40,1,0,0,0,42,43,1,0,0,0,43,45,1,0,0,0,44,42,1,0,0,0,45,46,5,
        6,0,0,46,47,5,9,0,0,47,48,3,4,2,0,48,3,1,0,0,0,49,78,5,10,0,0,50,
        54,5,1,0,0,51,53,3,4,2,0,52,51,1,0,0,0,53,56,1,0,0,0,54,52,1,0,0,
        0,54,55,1,0,0,0,55,57,1,0,0,0,56,54,1,0,0,0,57,78,5,2,0,0,58,62,
        5,3,0,0,59,61,3,4,2,0,60,59,1,0,0,0,61,64,1,0,0,0,62,60,1,0,0,0,
        62,63,1,0,0,0,63,65,1,0,0,0,64,62,1,0,0,0,65,78,5,2,0,0,66,67,5,
        4,0,0,67,68,5,10,0,0,68,69,3,4,2,0,69,70,5,2,0,0,70,78,1,0,0,0,71,
        72,5,5,0,0,72,73,5,10,0,0,73,74,3,4,2,0,74,75,3,4,2,0,75,76,5,2,
        0,0,76,78,1,0,0,0,77,49,1,0,0,0,77,50,1,0,0,0,77,58,1,0,0,0,77,66,
        1,0,0,0,77,71,1,0,0,0,78,5,1,0,0,0,10,9,16,21,24,29,38,42,54,62,
        77
    ]

class DsParser ( Parser ):

    grammarFileName = "Ds.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'(subscript'", "')'", "'(function'", 
                     "'(unary'", "'(binary'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "RULE", "WHITESPACE", "COMMENT", 
                      "NEWLINE", "SYMBOL" ]

    RULE_rule_pool = 0
    RULE_rule = 1
    RULE_term = 2

    ruleNames =  [ "rule_pool", "rule", "term" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    RULE=6
    WHITESPACE=7
    COMMENT=8
    NEWLINE=9
    SYMBOL=10

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class Rule_poolContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(DsParser.EOF, 0)

        def NEWLINE(self, i:int=None):
            if i is None:
                return self.getTokens(DsParser.NEWLINE)
            else:
                return self.getToken(DsParser.NEWLINE, i)

        def rule_(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(DsParser.RuleContext)
            else:
                return self.getTypedRuleContext(DsParser.RuleContext,i)


        def getRuleIndex(self):
            return DsParser.RULE_rule_pool

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRule_pool" ):
                return visitor.visitRule_pool(self)
            else:
                return visitor.visitChildren(self)




    def rule_pool(self):

        localctx = DsParser.Rule_poolContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_rule_pool)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 9
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,0,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 6
                    self.match(DsParser.NEWLINE) 
                self.state = 11
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,0,self._ctx)

            self.state = 24
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1146) != 0):
                self.state = 12
                self.rule_()
                self.state = 21
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,2,self._ctx)
                while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                    if _alt==1:
                        self.state = 14 
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)
                        while True:
                            self.state = 13
                            self.match(DsParser.NEWLINE)
                            self.state = 16 
                            self._errHandler.sync(self)
                            _la = self._input.LA(1)
                            if not (_la==9):
                                break

                        self.state = 18
                        self.rule_() 
                    self.state = 23
                    self._errHandler.sync(self)
                    _alt = self._interp.adaptivePredict(self._input,2,self._ctx)



            self.state = 29
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==9:
                self.state = 26
                self.match(DsParser.NEWLINE)
                self.state = 31
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 32
            self.match(DsParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RuleContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RULE(self):
            return self.getToken(DsParser.RULE, 0)

        def NEWLINE(self, i:int=None):
            if i is None:
                return self.getTokens(DsParser.NEWLINE)
            else:
                return self.getToken(DsParser.NEWLINE, i)

        def term(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(DsParser.TermContext)
            else:
                return self.getTypedRuleContext(DsParser.TermContext,i)


        def getRuleIndex(self):
            return DsParser.RULE_rule

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRule" ):
                return visitor.visitRule(self)
            else:
                return visitor.visitChildren(self)




    def rule_(self):

        localctx = DsParser.RuleContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_rule)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 42
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 1082) != 0):
                self.state = 34
                self.term()
                self.state = 36 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 35
                    self.match(DsParser.NEWLINE)
                    self.state = 38 
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not (_la==9):
                        break

                self.state = 44
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 45
            self.match(DsParser.RULE)
            self.state = 46
            self.match(DsParser.NEWLINE)
            self.state = 47
            self.term()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TermContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return DsParser.RULE_term

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class SymbolContext(TermContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a DsParser.TermContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def SYMBOL(self):
            return self.getToken(DsParser.SYMBOL, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSymbol" ):
                return visitor.visitSymbol(self)
            else:
                return visitor.visitChildren(self)


    class SubscriptContext(TermContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a DsParser.TermContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def term(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(DsParser.TermContext)
            else:
                return self.getTypedRuleContext(DsParser.TermContext,i)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSubscript" ):
                return visitor.visitSubscript(self)
            else:
                return visitor.visitChildren(self)


    class FunctionContext(TermContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a DsParser.TermContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def term(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(DsParser.TermContext)
            else:
                return self.getTypedRuleContext(DsParser.TermContext,i)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFunction" ):
                return visitor.visitFunction(self)
            else:
                return visitor.visitChildren(self)


    class BinaryContext(TermContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a DsParser.TermContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def SYMBOL(self):
            return self.getToken(DsParser.SYMBOL, 0)
        def term(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(DsParser.TermContext)
            else:
                return self.getTypedRuleContext(DsParser.TermContext,i)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBinary" ):
                return visitor.visitBinary(self)
            else:
                return visitor.visitChildren(self)


    class UnaryContext(TermContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a DsParser.TermContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def SYMBOL(self):
            return self.getToken(DsParser.SYMBOL, 0)
        def term(self):
            return self.getTypedRuleContext(DsParser.TermContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnary" ):
                return visitor.visitUnary(self)
            else:
                return visitor.visitChildren(self)



    def term(self):

        localctx = DsParser.TermContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_term)
        self._la = 0 # Token type
        try:
            self.state = 77
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [10]:
                localctx = DsParser.SymbolContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 49
                self.match(DsParser.SYMBOL)
                pass
            elif token in [1]:
                localctx = DsParser.SubscriptContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 50
                self.match(DsParser.T__0)
                self.state = 54
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while (((_la) & ~0x3f) == 0 and ((1 << _la) & 1082) != 0):
                    self.state = 51
                    self.term()
                    self.state = 56
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 57
                self.match(DsParser.T__1)
                pass
            elif token in [3]:
                localctx = DsParser.FunctionContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 58
                self.match(DsParser.T__2)
                self.state = 62
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while (((_la) & ~0x3f) == 0 and ((1 << _la) & 1082) != 0):
                    self.state = 59
                    self.term()
                    self.state = 64
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 65
                self.match(DsParser.T__1)
                pass
            elif token in [4]:
                localctx = DsParser.UnaryContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 66
                self.match(DsParser.T__3)
                self.state = 67
                self.match(DsParser.SYMBOL)
                self.state = 68
                self.term()
                self.state = 69
                self.match(DsParser.T__1)
                pass
            elif token in [5]:
                localctx = DsParser.BinaryContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 71
                self.match(DsParser.T__4)
                self.state = 72
                self.match(DsParser.SYMBOL)
                self.state = 73
                self.term()
                self.state = 74
                self.term()
                self.state = 75
                self.match(DsParser.T__1)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





