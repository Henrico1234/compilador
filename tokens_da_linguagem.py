# Literais e identificadores
INTEIRO = 'INTEIRO'
PONTO_FLUTUANTE = 'PONTO_FLUTUANTE'
CARACTERE_LITERAL = 'CARACTERE_LITERAL'
STRING_LITERAL = 'STRING_LITERAL'
BOOLEANO_LITERAL = 'BOOLEANO_LITERAL'
IDENTIFICADOR = 'IDENTIFICADOR'

#Palavras reservadas
INT = 'INT'
FLOAT = 'FLOAT'
CHAR = 'CHAR'
BOOL = 'BOOL'
STRING = 'STRING'
VOID = 'VOID'
IF = 'IF'
ELSE = 'ELSE'
WHILE = 'WHILE'
RETURN = 'RETURN'
TRUE = 'TRUE'
FALSE = 'FALSE'

#Operadores aritmeticos
MAIS = 'MAIS'
MENOS = 'MENOS'
MULTIPLICACAO = 'MULTIPLICACAO'
DIVISAO = 'DIVISAO'
RESTO = 'RESTO'

#Operadores relacionais, logicos e bit a bit
ATRIBUICAO = 'ATRIBUICAO'
IGUAL = 'IGUAL'
DIFERENTE = 'DIFERENTE'
MAIOR = 'MAIOR'
MENOR = 'MENOR'
MAIOR_IGUAL = 'MAIOR_IGUAL'
MENOR_IGUAL = 'MENOR_IGUAL'
E_LOGICO = 'E_LOGICO'
OU_LOGICO = 'OU_LOGICO'
NAO_LOGICO = 'NAO_LOGICO'
BIT_E = 'BIT_E'
BIT_OU = 'BIT_OU'
BIT_XOR = 'BIT_XOR'
BIT_NAO = 'BIT_NAO'

# Pontuacao e delimitadores
PONTO_VIRGULA = 'PONTO_VIRGULA'
VIRGULA = 'VIRGULA'
ABRE_PAREN = 'ABRE_PAREN'
FECHA_PAREN = 'FECHA_PAREN'
ABRE_CHAVE = 'ABRE_CHAVE'
FECHA_CHAVE = 'FECHA_CHAVE'
ABRE_COLCHETE = 'ABRE_COLCHETE'
FECHA_COLCHETE = 'FECHA_COLCHETE'

FIM_DE_ARQUIVO = 'FIM_DE_ARQUIVO'

TIPOS_PRIMITIVOS = {
    INT: 'int',
    FLOAT: 'float',
    CHAR: 'char',
    BOOL: 'bool',
    STRING: 'string',
    VOID: 'void',
}


class Token:
    def __init__(self, tipo, valor, linha=1, coluna=1):
        self.tipo = tipo
        self.valor = valor
        self.linha = linha
        self.coluna = coluna

    def __str__(self):
        return f"Token({self.tipo}, {repr(self.valor)}, linha={self.linha}, coluna={self.coluna})"

    __repr__ = __str__
