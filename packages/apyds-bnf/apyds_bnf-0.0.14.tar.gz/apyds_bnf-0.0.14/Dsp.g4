grammar Dsp;

rule_pool
    : NEWLINE* (rule (NEWLINE+ rule)*)? NEWLINE* EOF
    ;

rule
    : term
    | (term (',' term)*)? '=>' term
    ;

term
    : SYMBOL                                                 # symbol
    | '(' term ')'                                           # parentheses
    | term '::' term                                         # binary
    | term ('.' | '->') term                                 # binary
    | term '[' term (',' term)* ']'                          # subscript
    | term '(' (term (',' term)*)? ')'                       # function
    | <assoc=right> ('~' | '!' | '-' | '+' | '&' | '*') term # unary
    | term ('.*' | '->*') term                               # binary
    | term ('*' | '/' | '%') term                            # binary
    | term ('+' | '-') term                                  # binary
    | term ('<<' | '>>') term                                # binary
    | term ('<' | '>' | '<=' | '>=') term                    # binary
    | term ('==' | '!=') term                                # binary
    | term '&' term                                          # binary
    | term '^' term                                          # binary
    | term '|' term                                          # binary
    | term '&&' term                                         # binary
    | term '||' term                                         # binary
    | term '=' term                                          # binary
    ;

WHITESPACE
    : [ \t]+ -> skip
    ;

COMMENT
    : '//' ~[\r\n]* -> skip
    ;

NEWLINE
    : [\r\n]
    ;

SYMBOL
    : ~[ \t\r\n,()[\]]+
    ;
