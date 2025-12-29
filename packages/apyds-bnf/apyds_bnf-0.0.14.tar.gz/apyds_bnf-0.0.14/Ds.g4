grammar Ds;

rule_pool
    : NEWLINE* (rule (NEWLINE+ rule)*)? NEWLINE* EOF
    ;

rule
    : (term NEWLINE+)* RULE NEWLINE term
    ;

term
    : SYMBOL                         # symbol
    | '(subscript' term* ')'         # subscript
    | '(function' term* ')'          # function
    | '(unary' SYMBOL term ')'       # unary
    | '(binary' SYMBOL term term ')' # binary
    ;

RULE
    : '--' '-'*
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
