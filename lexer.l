%{


#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef STANDALONE
  #include "parser.tab.h"   
#else

  enum {
    TOK_INT = 258, TOK_FLOAT, TOK_DOUBLE, TOK_CHAR, TOK_BOOL,
    TOK_VOID, TOK_LONG, TOK_SHORT, TOK_UNSIGNED, TOK_SIGNED,
    TOK_CONST, TOK_AUTO, TOK_RETURN, TOK_IF, TOK_ELSE,
    TOK_WHILE, TOK_FOR, TOK_DO, TOK_BREAK, TOK_CONTINUE,
    TOK_SWITCH, TOK_CASE, TOK_DEFAULT, TOK_STRUCT, TOK_CLASS,
    TOK_PUBLIC, TOK_PRIVATE, TOK_PROTECTED, TOK_NEW, TOK_DELETE,
    TOK_NAMESPACE, TOK_USING, TOK_TEMPLATE, TOK_TYPENAME,
    TOK_TRY, TOK_CATCH, TOK_THROW, TOK_INCLUDE, TOK_DEFINE,
    
    TOK_INTEGER_LIT, TOK_FLOAT_LIT, TOK_STRING_LIT, TOK_CHAR_LIT,
    
    TOK_IDENTIFIER,
    
    TOK_INC, TOK_DEC,
    TOK_AND, TOK_OR,
    TOK_EQ,  TOK_NEQ,
    TOK_LEQ, TOK_GEQ,
    TOK_LSHIFT, TOK_RSHIFT,
    TOK_ARROW, TOK_SCOPE,
    TOK_PLUS_EQ, TOK_MINUS_EQ, TOK_MUL_EQ,
    TOK_DIV_EQ,  TOK_MOD_EQ,
    TOK_AND_EQ,  TOK_OR_EQ,   TOK_XOR_EQ,
    TOK_LSHIFT_EQ, TOK_RSHIFT_EQ,
    
    TOK_PREPROCESSOR, TOK_COMMENT
  };
#endif


#ifndef STANDALONE
 
#else
  typedef union {
    int    ival;
    double fval;
    char  *sval;
  } YYSTYPE;
  YYSTYPE yylval;
#endif

/* ── Global log file ── */
static FILE *log_fp = NULL;

/* ── Line / column tracking ── */
static int yyline = 1;
static int yycol  = 1;
static int prev_col = 1;

/* ── Helpers ── */
static void log_token(const char *category, const char *value);
static void update_col(void);

%}


%option noyywrap
%option yylineno
%option nounput
%option noinput


DIGIT        [0-9]
LETTER       [a-zA-Z_]
ALNUM        [a-zA-Z0-9_]
HEX_DIGIT    [0-9a-fA-F]
OCT_DIGIT    [0-7]
BIN_DIGIT    [01]

/* Integer suffixes */
INT_SUFFIX   ([uU]?[lL]{0,2}|[lL]{0,2}[uU]?)

/* Number literals */
DEC_INT      [1-9]{DIGIT}*{INT_SUFFIX}?
HEX_INT      0[xX]{HEX_DIGIT}+{INT_SUFFIX}?
OCT_INT      0{OCT_DIGIT}*{INT_SUFFIX}?
BIN_INT      0[bB]{BIN_DIGIT}+{INT_SUFFIX}?

/* Float literals */
FLOAT_SUFFIX [fFlL]?
FLOAT_LIT    ({DIGIT}+\.{DIGIT}*|\.{DIGIT}+)([eE][+-]?{DIGIT}+)?{FLOAT_SUFFIX}

/* String / char escape sequences */
ESC_SEQ      \\(['"\\?abfnrtv]|[0-7]{1,3}|x{HEX_DIGIT}+)

%%

\n          { yyline++; yycol = 1; /* newline resets column */ }
[ \t\r]+    { yycol += yyleng; /* consume whitespace silently */ }



"//"[^\n]*  {
                log_token("COMMENT (line)", yytext);
                yycol += yyleng;
            }

"/*"([^*]|\*[^/])*"*/"  {
                /* Count newlines inside block comment */
                int i;
                for (i = 0; yytext[i]; i++)
                    if (yytext[i] == '\n') { yyline++; yycol = 1; }
                    else yycol++;
                log_token("COMMENT (block)", yytext);
                /* return TOK_COMMENT; */
            }



^[ \t]*"#"[^\n]*  {
                log_token("PREPROCESSOR", yytext);
                yycol += yyleng;
            }



"int"           { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_INT;       }
"float"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_FLOAT;     }
"double"        { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_DOUBLE;    }
"char"          { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_CHAR;      }
"bool"          { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_BOOL;      }
"void"          { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_VOID;      }
"long"          { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_LONG;      }
"short"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_SHORT;     }
"unsigned"      { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_UNSIGNED;  }
"signed"        { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_SIGNED;    }
"const"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_CONST;     }
"auto"          { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_AUTO;      }
"return"        { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_RETURN;    }
"if"            { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_IF;        }
"else"          { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_ELSE;      }
"while"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_WHILE;     }
"for"           { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_FOR;       }
"do"            { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_DO;        }
"break"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_BREAK;     }
"continue"      { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_CONTINUE;  }
"switch"        { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_SWITCH;    }
"case"          { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_CASE;      }
"default"       { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_DEFAULT;   }
"struct"        { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_STRUCT;    }
"class"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_CLASS;     }
"public"        { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_PUBLIC;    }
"private"       { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_PRIVATE;   }
"protected"     { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_PROTECTED; }
"new"           { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_NEW;       }
"delete"        { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_DELETE;    }
"namespace"     { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_NAMESPACE; }
"using"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_USING;     }
"template"      { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_TEMPLATE;  }
"typename"      { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_TYPENAME;  }
"try"           { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_TRY;       }
"catch"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_CATCH;     }
"throw"         { log_token("KEYWORD", yytext); yycol+=yyleng; return TOK_THROW;     }



{LETTER}{ALNUM}*  {
                yylval.sval = strdup(yytext);
                log_token("IDENTIFIER", yytext);
                yycol += yyleng;
                return TOK_IDENTIFIER;
            }



{FLOAT_LIT}     {
                yylval.fval = atof(yytext);
                log_token("FLOAT_LITERAL", yytext);
                yycol += yyleng;
                return TOK_FLOAT_LIT;
            }

{HEX_INT}       {
                yylval.ival = (int)strtol(yytext, NULL, 16);
                log_token("INTEGER_LITERAL (hex)", yytext);
                yycol += yyleng;
                return TOK_INTEGER_LIT;
            }

{BIN_INT}       {
                yylval.ival = (int)strtol(yytext+2, NULL, 2);
                log_token("INTEGER_LITERAL (bin)", yytext);
                yycol += yyleng;
                return TOK_INTEGER_LIT;
            }

{OCT_INT}       {
                yylval.ival = (int)strtol(yytext, NULL, 8);
                log_token("INTEGER_LITERAL (oct)", yytext);
                yycol += yyleng;
                return TOK_INTEGER_LIT;
            }

{DEC_INT}       {
                yylval.ival = atoi(yytext);
                log_token("INTEGER_LITERAL", yytext);
                yycol += yyleng;
                return TOK_INTEGER_LIT;
            }

"0"             {
                yylval.ival = 0;
                log_token("INTEGER_LITERAL", yytext);
                yycol += yyleng;
                return TOK_INTEGER_LIT;
            }



\"({ESC_SEQ}|[^"\\])*\"   {
                yylval.sval = strdup(yytext);
                log_token("STRING_LITERAL", yytext);
                yycol += yyleng;
                return TOK_STRING_LIT;
            }

 /* Raw string: R"delimiter(...)delimiter"  (C++11) */
R\"[^(]*\(([^)]*|\)[^"])*\)\"  {
                yylval.sval = strdup(yytext);
                log_token("STRING_LITERAL (raw)", yytext);
                yycol += yyleng;
                return TOK_STRING_LIT;
            }

 /* Unterminated string — recover gracefully */
\"[^\"\n]*\n    {
                fprintf(stderr, "Lexer warning: unterminated string at line %d\n", yyline);
                yyline++; yycol = 1;
            }



\'({ESC_SEQ}|[^'\\])\'  {
                yylval.sval = strdup(yytext);
                log_token("CHAR_LITERAL", yytext);
                yycol += yyleng;
                return TOK_CHAR_LIT;
            }



"<<"    { log_token("OPERATOR", yytext); yycol+=2; return TOK_LSHIFT;    }
">>"    { log_token("OPERATOR", yytext); yycol+=2; return TOK_RSHIFT;    }
"<="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_LEQ;       }
">="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_GEQ;       }
"=="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_EQ;        }
"!="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_NEQ;       }
"&&"    { log_token("OPERATOR", yytext); yycol+=2; return TOK_AND;       }
"||"    { log_token("OPERATOR", yytext); yycol+=2; return TOK_OR;        }
"++"    { log_token("OPERATOR", yytext); yycol+=2; return TOK_INC;       }
"--"    { log_token("OPERATOR", yytext); yycol+=2; return TOK_DEC;       }
"->"    { log_token("OPERATOR", yytext); yycol+=2; return TOK_ARROW;     }
"::"    { log_token("OPERATOR", yytext); yycol+=2; return TOK_SCOPE;     }
"+="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_PLUS_EQ;   }
"-="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_MINUS_EQ;  }
"*="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_MUL_EQ;    }
"/="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_DIV_EQ;    }
"%="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_MOD_EQ;    }
"&="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_AND_EQ;    }
"|="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_OR_EQ;     }
"^="    { log_token("OPERATOR", yytext); yycol+=2; return TOK_XOR_EQ;    }
"<<="   { log_token("OPERATOR", yytext); yycol+=3; return TOK_LSHIFT_EQ; }
">>="   { log_token("OPERATOR", yytext); yycol+=3; return TOK_RSHIFT_EQ; }



"+"     { log_token("OPERATOR", "+");  yycol++; return '+'; }
"-"     { log_token("OPERATOR", "-");  yycol++; return '-'; }
"*"     { log_token("OPERATOR", "*");  yycol++; return '*'; }
"/"     { log_token("OPERATOR", "/");  yycol++; return '/'; }
"%"     { log_token("OPERATOR", "%");  yycol++; return '%'; }
"="     { log_token("OPERATOR", "=");  yycol++; return '='; }
"<"     { log_token("OPERATOR", "<");  yycol++; return '<'; }
">"     { log_token("OPERATOR", ">");  yycol++; return '>'; }
"!"     { log_token("OPERATOR", "!");  yycol++; return '!'; }
"&"     { log_token("OPERATOR", "&");  yycol++; return '&'; }
"|"     { log_token("OPERATOR", "|");  yycol++; return '|'; }
"^"     { log_token("OPERATOR", "^");  yycol++; return '^'; }
"~"     { log_token("OPERATOR", "~");  yycol++; return '~'; }
"?"     { log_token("OPERATOR", "?");  yycol++; return '?'; }



"("     { log_token("PUNCTUATION", "("); yycol++; return '('; }
")"     { log_token("PUNCTUATION", ")"); yycol++; return ')'; }
"{"     { log_token("PUNCTUATION", "{"); yycol++; return '{'; }
"}"     { log_token("PUNCTUATION", "}"); yycol++; return '}'; }
"["     { log_token("PUNCTUATION", "["); yycol++; return '['; }
"]"     { log_token("PUNCTUATION", "]"); yycol++; return ']'; }
";"     { log_token("PUNCTUATION", ";"); yycol++; return ';'; }
":"     { log_token("PUNCTUATION", ":"); yycol++; return ':'; }
","     { log_token("PUNCTUATION", ","); yycol++; return ','; }
"."     { log_token("PUNCTUATION", "."); yycol++; return '.'; }



.       {
            char buf[32];
            snprintf(buf, sizeof(buf), "%s (unknown)", yytext);
            log_token("UNKNOWN", buf);
            fprintf(stderr,
                "Lexer error: unexpected character '%s' at line %d, col %d\n",
                yytext, yyline, yycol);
            yycol++;
        }

%%


static void log_token(const char *category, const char *value)
{
    if (!log_fp) return;

    /* Escape control characters in value for safe printing */
    char safe[512];
    int  si = 0;
    const char *p = value;
    while (*p && si < (int)sizeof(safe) - 4) {
        if (*p == '\n')       { safe[si++] = '\\'; safe[si++] = 'n'; }
        else if (*p == '\t')  { safe[si++] = '\\'; safe[si++] = 't'; }
        else if (*p == '\r')  { safe[si++] = '\\'; safe[si++] = 'r'; }
        else                   safe[si++] = *p;
        p++;
    }
    safe[si] = '\0';

    fprintf(log_fp, "%-6d  %-5d  %-28s  %s\n",
            yyline, yycol, category, safe);
}

/*
 * open_log  — called from main() or yylex_init() before scanning starts.
 * Creates (or overwrites) lexer_output.txt.
 */
void open_log(const char *filename)
{
    log_fp = fopen(filename ? filename : "lexer_output.txt", "w");
    if (!log_fp) {
        fprintf(stderr, "Warning: cannot open log file — proceeding without it.\n");
        return;
    }

    fprintf(log_fp,
        "\n"
        "  C++ Lexical Analysis Output\n"
        "  Generated by lexer.l  (Flex)\n"
        
        "  Format: Line   Col   Token Category              Value\n"
        "\n");
}


void close_log(void)
{
    if (!log_fp) return;
    fprintf(log_fp,
        "\n"
        "  End of lexical analysis.\n"
        "\n");
    fclose(log_fp);
    log_fp = NULL;
}



#ifdef STANDALONE

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <source.cpp>\n", argv[0]);
        return 1;
    }

    FILE *src = fopen(argv[1], "r");
    if (!src) {
        fprintf(stderr, "Error: cannot open '%s'\n", argv[1]);
        return 1;
    }

    yyin = src;          
    open_log("lexer_output.txt");

    printf("Analysing: %s\n", argv[1]);
    printf("%-6s  %-5s  %-28s  %s\n", "Line", "Col", "Category", "Value");
    printf("%.70s\n", "----------------------------------------------------------------------");

   
    FILE *old_fp = log_fp;
    log_fp = stdout;       

    int tok;
    while ((tok = yylex()) != 0) {
        /* For demonstration, we print the token type as well. */
        // printf("Token: %d\n", tok);
    }

    log_fp = old_fp;       /* restore log file output */
    rewind(src);
    yyin   = src;
    yyline = 1;
    yycol  = 1;
    open_log("lexer_output.txt");
    while (yylex() != 0) {}
    close_log();

    fclose(src);
    printf("\nDone. Token log written to: lexer_output.txt\n");
    return 0;
}

#endif 
