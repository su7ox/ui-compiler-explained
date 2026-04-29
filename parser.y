
%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Declarations from the lexer */
extern int  yylex(void);
extern int  yylineno;
extern char *yytext;
extern void open_log(const char *filename);
extern void close_log(void);

void yyerror(const char *msg);
%}

%union {
    int    ival;
    double fval;
    char  *sval;
}



%token TOK_INT TOK_FLOAT TOK_DOUBLE TOK_CHAR TOK_BOOL
%token TOK_VOID TOK_LONG TOK_SHORT TOK_UNSIGNED TOK_SIGNED
%token TOK_CONST TOK_AUTO TOK_RETURN
%token TOK_IF TOK_ELSE TOK_WHILE TOK_FOR TOK_DO
%token TOK_BREAK TOK_CONTINUE TOK_SWITCH TOK_CASE TOK_DEFAULT
%token TOK_STRUCT TOK_CLASS TOK_PUBLIC TOK_PRIVATE TOK_PROTECTED
%token TOK_NEW TOK_DELETE TOK_NAMESPACE TOK_USING
%token TOK_TEMPLATE TOK_TYPENAME TOK_TRY TOK_CATCH TOK_THROW
%token TOK_INCLUDE TOK_DEFINE


%token <ival> TOK_INTEGER_LIT
%token <fval> TOK_FLOAT_LIT
%token <sval> TOK_STRING_LIT
%token <sval> TOK_CHAR_LIT


%token <sval> TOK_IDENTIFIER


%token TOK_INC TOK_DEC
%token TOK_AND TOK_OR
%token TOK_EQ  TOK_NEQ
%token TOK_LEQ TOK_GEQ
%token TOK_LSHIFT TOK_RSHIFT
%token TOK_ARROW TOK_SCOPE
%token TOK_PLUS_EQ TOK_MINUS_EQ TOK_MUL_EQ
%token TOK_DIV_EQ  TOK_MOD_EQ
%token TOK_AND_EQ  TOK_OR_EQ   TOK_XOR_EQ
%token TOK_LSHIFT_EQ TOK_RSHIFT_EQ


%right '=' TOK_PLUS_EQ TOK_MINUS_EQ TOK_MUL_EQ TOK_DIV_EQ TOK_MOD_EQ
%right TOK_AND_EQ TOK_OR_EQ TOK_XOR_EQ TOK_LSHIFT_EQ TOK_RSHIFT_EQ
%left  TOK_OR
%left  TOK_AND
%left  '|'
%left  '^'
%left  '&'
%left  TOK_EQ TOK_NEQ
%left  '<' '>' TOK_LEQ TOK_GEQ
%left  TOK_LSHIFT TOK_RSHIFT
%left  '+' '-'
%left  '*' '/' '%'
%right '!' '~' TOK_INC TOK_DEC UMINUS
%left  '(' ')' '[' ']' TOK_ARROW '.' TOK_SCOPE


%type <sval> type_spec expr unary_expr primary_expr

%%

// GRAMMAR RULES

program
    : 
    | program top_level_decl
    ;

top_level_decl
    : namespace_decl
    | using_decl
    | class_decl
    | struct_decl
    | function_def
    | var_decl
    | ';'                        
    ;

namespace_decl
    : TOK_NAMESPACE TOK_IDENTIFIER '{' program '}'
    ;

using_decl
    : TOK_USING TOK_NAMESPACE TOK_IDENTIFIER ';'
    | TOK_USING TOK_IDENTIFIER TOK_SCOPE TOK_IDENTIFIER ';'
    ;


/* Class / Struct */
class_decl
    : TOK_CLASS TOK_IDENTIFIER '{' member_list '}' ';'
    | TOK_CLASS TOK_IDENTIFIER ':' access_spec TOK_IDENTIFIER
      '{' member_list '}' ';'
    ;

struct_decl
    : TOK_STRUCT TOK_IDENTIFIER '{' member_list '}' ';'
    ;

access_spec
    : TOK_PUBLIC | TOK_PRIVATE | TOK_PROTECTED
    ;

member_list
    : /* empty */
    | member_list member_decl
    ;

member_decl
    : access_spec ':'
    | var_decl
    | function_def
    | function_proto
    ;


/* Type specifiers  */
type_spec
    : TOK_INT       { $$ = "int";      }
    | TOK_FLOAT     { $$ = "float";    }
    | TOK_DOUBLE    { $$ = "double";   }
    | TOK_CHAR      { $$ = "char";     }
    | TOK_BOOL      { $$ = "bool";     }
    | TOK_VOID      { $$ = "void";     }
    | TOK_LONG      { $$ = "long";     }
    | TOK_SHORT     { $$ = "short";    }
    | TOK_UNSIGNED  { $$ = "unsigned"; }
    | TOK_SIGNED    { $$ = "signed";   }
    | TOK_CONST type_spec { $$ = $2;   }
    | TOK_AUTO      { $$ = "auto";     }
    | TOK_IDENTIFIER { $$ = $1;        }   
    ;



var_decl
    : type_spec TOK_IDENTIFIER ';'
    | type_spec TOK_IDENTIFIER '=' expr ';'
    | type_spec TOK_IDENTIFIER '[' expr ']' ';'
    | type_spec '*' TOK_IDENTIFIER ';'
    | type_spec '*' TOK_IDENTIFIER '=' expr ';'
    | type_spec '&' TOK_IDENTIFIER '=' expr ';'
    ;



function_proto
    : type_spec TOK_IDENTIFIER '(' param_list ')' ';'
    ;


function_def
    : type_spec TOK_IDENTIFIER '(' param_list ')' compound_stmt
    ;

param_list
    : /* empty */
    | param
    | param_list ',' param
    ;

param
    : type_spec TOK_IDENTIFIER
    | type_spec TOK_IDENTIFIER '=' expr
    | type_spec TOK_IDENTIFIER '[' ']'
    | type_spec '*' TOK_IDENTIFIER
    | type_spec '&' TOK_IDENTIFIER
    | type_spec                        
    ;


/* Statements */
compound_stmt
    : '{' stmt_list '}'
    ;

stmt_list
    : /* empty */
    | stmt_list stmt
    ;

stmt
    : var_decl
    | expr ';'
    | compound_stmt
    | if_stmt
    | while_stmt
    | for_stmt
    | do_stmt
    | return_stmt
    | break_stmt
    | continue_stmt
    | switch_stmt
    | try_stmt
    | ';'
    ;

if_stmt
    : TOK_IF '(' expr ')' stmt
    | TOK_IF '(' expr ')' stmt TOK_ELSE stmt
    ;

while_stmt
    : TOK_WHILE '(' expr ')' stmt
    ;

for_stmt
    : TOK_FOR '(' for_init expr ';' expr ')' stmt
    | TOK_FOR '(' for_init     ';' expr ')' stmt
    | TOK_FOR '(' for_init expr ';'     ')' stmt
    | TOK_FOR '(' for_init     ';'      ')' stmt
    ;

for_init
    : var_decl
    | expr ';'
    | ';'
    ;

do_stmt
    : TOK_DO stmt TOK_WHILE '(' expr ')' ';'
    ;

return_stmt
    : TOK_RETURN expr ';'
    | TOK_RETURN ';'
    ;

break_stmt    : TOK_BREAK ';' ;
continue_stmt : TOK_CONTINUE ';' ;

switch_stmt
    : TOK_SWITCH '(' expr ')' '{' case_list '}'
    ;

case_list
    : /* empty */
    | case_list case_item
    ;

case_item
    : TOK_CASE expr ':' stmt_list
    | TOK_DEFAULT   ':' stmt_list
    ;

try_stmt
    : TOK_TRY compound_stmt catch_list
    ;

catch_list
    : catch_clause
    | catch_list catch_clause
    ;

catch_clause
    : TOK_CATCH '(' param ')' compound_stmt
    | TOK_CATCH '(' '.' '.' '.' ')' compound_stmt
    ;


/* Expressions */
expr
    : expr '='          expr  { $$ = $1; }
    | expr TOK_PLUS_EQ  expr  { $$ = $1; }
    | expr TOK_MINUS_EQ expr  { $$ = $1; }
    | expr TOK_MUL_EQ   expr  { $$ = $1; }
    | expr TOK_DIV_EQ   expr  { $$ = $1; }
    | expr TOK_MOD_EQ   expr  { $$ = $1; }
    | expr TOK_AND_EQ   expr  { $$ = $1; }
    | expr TOK_OR_EQ    expr  { $$ = $1; }
    | expr TOK_XOR_EQ   expr  { $$ = $1; }
    | expr TOK_LSHIFT_EQ expr { $$ = $1; }
    | expr TOK_RSHIFT_EQ expr { $$ = $1; }
    | expr TOK_OR       expr  { $$ = $1; }
    | expr TOK_AND      expr  { $$ = $1; }
    | expr '|'          expr  { $$ = $1; }
    | expr '^'          expr  { $$ = $1; }
    | expr '&'          expr  { $$ = $1; }
    | expr TOK_EQ       expr  { $$ = $1; }
    | expr TOK_NEQ      expr  { $$ = $1; }
    | expr '<'          expr  { $$ = $1; }
    | expr '>'          expr  { $$ = $1; }
    | expr TOK_LEQ      expr  { $$ = $1; }
    | expr TOK_GEQ      expr  { $$ = $1; }
    | expr TOK_LSHIFT   expr  { $$ = $1; }
    | expr TOK_RSHIFT   expr  { $$ = $1; }
    | expr '+'          expr  { $$ = $1; }
    | expr '-'          expr  { $$ = $1; }
    | expr '*'          expr  { $$ = $1; }
    | expr '/'          expr  { $$ = $1; }
    | expr '%'          expr  { $$ = $1; }
    | expr '?' expr ':' expr  { $$ = $1; }
    | expr '[' expr ']'       { $$ = $1; }
    | expr '.' TOK_IDENTIFIER { $$ = $1; }
    | expr TOK_ARROW TOK_IDENTIFIER { $$ = $1; }
    | expr TOK_SCOPE TOK_IDENTIFIER { $$ = $1; }
    | expr '(' arg_list ')'   { $$ = $1; }   
    | unary_expr              { $$ = $1; }
    ;

unary_expr
    : '-' expr %prec UMINUS  { $$ = $2; }
    | '+' expr %prec UMINUS  { $$ = $2; }
    | '!' expr               { $$ = $2; }
    | '~' expr               { $$ = $2; }
    | '*' expr %prec UMINUS  { $$ = $2; }   
    | '&' expr %prec UMINUS  { $$ = $2; }   
    | TOK_INC expr           { $$ = $2; }
    | TOK_DEC expr           { $$ = $2; }
    | primary_expr           { $$ = $1; }
    ;

primary_expr
    : TOK_INTEGER_LIT        { $$ = "int_lit";    }
    | TOK_FLOAT_LIT          { $$ = "float_lit";  }
    | TOK_STRING_LIT         { $$ = $1;           }
    | TOK_CHAR_LIT           { $$ = $1;           }
    | TOK_IDENTIFIER         { $$ = $1;           }
    | '(' expr ')'           { $$ = $2;           }
    | TOK_NEW type_spec      { $$ = "new_expr";   }
    | TOK_DELETE expr        { $$ = "del_expr";   }
    ;

arg_list
    : /* empty */
    | expr
    | arg_list ',' expr
    ;

%%


void yyerror(const char *msg)
{
    fprintf(stderr, "Parse error at line %d: %s (near '%s')\n",
            yylineno, msg, yytext);
}
main — entry point when parser is the driver
int main(int argc, char *argv[])
{
    extern FILE *yyin;

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <source.cpp>\n", argv[0]);
        return 1;
    }

    yyin = fopen(argv[1], "r");
    if (!yyin) {
        fprintf(stderr, "Cannot open '%s'\n", argv[1]);
        return 1;
    }

    open_log("lexer_output.txt");   
    int result = yyparse();         
    close_log();                   

    fclose(yyin);

    if (result == 0)
        printf("Parsing successful. Token log → lexer_output.txt\n");
    else
        printf("Parsing finished with errors. Token log → lexer_output.txt\n");

    return result;
}
