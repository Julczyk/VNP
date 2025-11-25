grammar SRAPL;

// ============
// PARSER RULES
// ============

program
    : statement* EOF
    ;

statement
    : block                 # BlockStmt
    | assignment ';'        # AssignStmt   // Średnik wymagany
    | ifStatement           # IfStmt       // IF ma własne klamry, nie wymaga średnika
    | controlCommand ';'    # ControlStmt  // Średnik wymagany
    | actionCall ';'        # ActionStmt   // Średnik wymagany
    ;

block
    : '{' statement* '}'
    ;

assignment
    : memoryCell '=' expr
    ;

ifStatement
    : IF '(' expr ')' block
    ;

controlCommand
    : REDO
    | RESTART
    ;

actionCall
    : FunctionID '(' (expr (',' expr)*)? ')'
    ;

memoryCell
    : MEM_TAG '[' expr ']'
    ;

expr
    : '(' expr ')'              # ParenExpr
    | memoryCell                # MemoryExpr
    | Number                    # NumberExpr
    | '-' expr                  # UnaryMinusExpr
    | <assoc=right> expr '**' expr  # PowerExpr
    | expr ('*'|'/') expr       # MulDivExpr
    | expr ('+'|'-') expr       # AddSubExpr
    ;

// ===========
// LEXER RULES
// ===========

IF      : 'IF';
REDO    : 'REDO';
RESTART : 'RESTART';

MEM_TAG : [xX];
FunctionID : 'f_' [0-9]+;

// Liczby (tylko wartość bezwzględna, znak obsługuje parser)
Number
    : [0-9]+ ('.' [0-9]+)?
    ;

// Średnik jako osobny token
SEMI : ';';

WS
    : [ \t\r\n]+ -> skip
    ;

COMMENT
    : '#' ~[\r\n]* -> skip
    ;