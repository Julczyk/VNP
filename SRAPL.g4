grammar SRAPL;

/*
 * Parser Rules
 */

// Główny punkt wejścia
file
    : partsSection programmSection EOF
    ;

// --- Sekcja części ---
// Zgodnie z opisem: $PARTS: lista floatów oddzielona przecinkami, kończy się średnikiem.
// Uwzględniono elastyczność (dwukropek opcjonalny, jak w przykładzie).
partsSection
    : PARTS_HEADER floatList SEMI
    ;

floatList
    : value (COMMA value)*
    ;

// Wartość liczbowa (akceptujemy int jako float, np. 0 zamiast 0.0)
value
    : FLOAT
    | INT
    ;

// --- Sekcja programu ---
programmSection
    : PROGRAM_HEADER blockContent
    ;

// Zawartość bloku kodu (lista instrukcji)
blockContent
    : statement*
    ;

// Pojedyncza instrukcja
statement
    : assignment      // Przypisanie: X[i] = ...
    | functionCall    // Wywołanie: f_n(...)
    | ifStatement     // Warunek: IF(...) { ... }
    | redoStatement   // Pętla: REDO
    | restartStatement // Restart: RESTART
    | block           // Zagnieżdżony blok: { ... }
    ;

// Blok kodu w klamrach
block
    : LBRACE blockContent RBRACE
    ;

// Przypisanie wartości do pamięci
assignment
    : memoryRef ASSIGN expression SEMI
    ;

// Wywołanie funkcji części (kończy krok, ale gramatycznie to po prostu instrukcja)
functionCall
    : FUNC_ID LPAREN argList? RPAREN SEMI
    ;

argList
    : expression (COMMA expression)*
    ;

// Instrukcja warunkowa
ifStatement
    : IF LPAREN expression RPAREN block
    ;

// Słowa kluczowe sterujące przepływem
redoStatement
    : REDO SEMI
    ;

restartStatement
    : RESTART SEMI
    ;

// Odwołanie do pamięci X[i]
memoryRef
    : MEM_TAG LBRACK INT RBRACK
    ;

// Wyrażenia matematyczne
expression
    : LPAREN expression RPAREN             # parensExpr
    | expression POWER expression          # powerExpr
    | expression (MUL | DIV) expression    # mulDivExpr
    | expression (PLUS | MINUS) expression # addSubExpr
    | memoryRef                            # variableExpr
    | value                                # atomExpr
    ;

/*
 * Lexer Rules
 */

// Nagłówki sekcji
PARTS_HEADER: '$PARTS' ':'? ; // Dwukropek opcjonalny, aby pasował i do opisu i do przykładu
PROGRAM_HEADER: '$PROGRAMM' ;

// Słowa kluczowe
IF: 'IF' ;
REDO: 'REDO' ;
RESTART: 'RESTART' ;

// Identyfikatory
MEM_TAG: 'X' ;             // Oznaczenie pamięci
FUNC_ID: 'f_' [0-9]+ ;     // Funkcje postaci f_0, f_1, f_12

// Operatory
ASSIGN: '=' ;
PLUS:   '+' ;
MINUS:  '-' ;
MUL:    '*' ;
DIV:    '/' ;
POWER:  '**' ;

// Separatory
LPAREN: '(' ;
RPAREN: ')' ;
LBRACE: '{' ;
RBRACE: '}' ;
LBRACK: '[' ;
RBRACK: ']' ;
SEMI:   ';' ;
COMMA:  ',' ;

// Liczby
FLOAT
    : [0-9]+ '.' [0-9]*
    | '.' [0-9]+
    ;

INT
    : [0-9]+
    ;

// Komentarze (ignorowane)
COMMENT
    : '#' ~[\r\n]* -> skip
    ;

// Białe znaki (ignorowane)
WS
    : [ \t\r\n]+ -> skip
    ;