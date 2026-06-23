from tokens_da_linguagem import *

PALAVRAS_RESERVADAS = {
    'int': INT,
    'float': FLOAT,
    'char': CHAR,
    'bool': BOOL,
    'string': STRING,
    'void': VOID,
    'if': IF,
    'else': ELSE,
    'while': WHILE,
    'return': RETURN,
    'true': TRUE,
    'false': FALSE,
}

ESCAPES = {
    'n': '\n',
    't': '\t',
    'r': '\r',
    '0': '\0',
    "'": "'",
    '"': '"',
    '\\': '\\',
}


class AnalisadorLexico:
    def __init__(self, texto):
        self.texto = texto
        self.posicao = 0
        self.linha = 1
        self.coluna = 1
        self.caractere_atual = self.texto[self.posicao] if self.texto else None

    def erro(self, mensagem):
        raise Exception(f"Erro Lexico na linha {self.linha}, coluna {self.coluna}: {mensagem}")

    def avancar(self):
        if self.caractere_atual == '\n':
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        self.posicao += 1
        if self.posicao >= len(self.texto):
            self.caractere_atual = None
        else:
            self.caractere_atual = self.texto[self.posicao]

    def espiar(self):
        posicao_espiar = self.posicao + 1
        if posicao_espiar >= len(self.texto):
            return None
        return self.texto[posicao_espiar]

    def pular_espaco_em_branco(self):
        while self.caractere_atual is not None and self.caractere_atual.isspace():
            self.avancar()

    def pular_comentario_linha(self):
        while self.caractere_atual is not None and self.caractere_atual != '\n':
            self.avancar()

    def pular_comentario_bloco(self):
        self.avancar()
        self.avancar()
        while self.caractere_atual is not None:
            if self.caractere_atual == '*' and self.espiar() == '/':
                self.avancar()
                self.avancar()
                return
            self.avancar()
        self.erro("comentario de bloco nao finalizado")

    def numero(self):
        linha_inicial = self.linha
        coluna_inicial = self.coluna
        resultado = ''

        while self.caractere_atual is not None and self.caractere_atual.isdigit():
            resultado += self.caractere_atual
            self.avancar()

        if self.caractere_atual == '.':
            resultado += '.'
            self.avancar()
            if self.caractere_atual is None or not self.caractere_atual.isdigit():
                self.erro("numero de ponto flutuante mal formado")
            while self.caractere_atual is not None and self.caractere_atual.isdigit():
                resultado += self.caractere_atual
                self.avancar()
            return Token(PONTO_FLUTUANTE, float(resultado), linha_inicial, coluna_inicial)

        return Token(INTEIRO, int(resultado), linha_inicial, coluna_inicial)

    def identificador_ou_palavra_reservada(self):
        linha_inicial = self.linha
        coluna_inicial = self.coluna
        resultado = ''

        while self.caractere_atual is not None and (
            self.caractere_atual.isalnum() or self.caractere_atual == '_'
        ):
            resultado += self.caractere_atual
            self.avancar()

        tipo = PALAVRAS_RESERVADAS.get(resultado, IDENTIFICADOR)
        if tipo == TRUE:
            return Token(BOOLEANO_LITERAL, True, linha_inicial, coluna_inicial)
        if tipo == FALSE:
            return Token(BOOLEANO_LITERAL, False, linha_inicial, coluna_inicial)
        return Token(tipo, resultado, linha_inicial, coluna_inicial)

    def ler_escape(self):
        self.avancar()
        if self.caractere_atual is None:
            self.erro("sequencia de escape nao finalizada")
        valor = ESCAPES.get(self.caractere_atual)
        if valor is None:
            self.erro(f"escape invalido '\\{self.caractere_atual}'")
        self.avancar()
        return valor

    def literal_caractere(self):
        linha_inicial = self.linha
        coluna_inicial = self.coluna

        self.avancar()
        if self.caractere_atual is None:
            self.erro("literal de caractere nao finalizado")

        if self.caractere_atual == '\\':
            valor = self.ler_escape()
        else:
            valor = self.caractere_atual
            self.avancar()

        if self.caractere_atual != "'":
            self.erro("literal de caractere deve conter exatamente um caractere")
        self.avancar()
        return Token(CARACTERE_LITERAL, valor, linha_inicial, coluna_inicial)

    def literal_string(self):
        linha_inicial = self.linha
        coluna_inicial = self.coluna
        resultado = ''

        self.avancar()
        while self.caractere_atual is not None and self.caractere_atual != '"':
            if self.caractere_atual == '\\':
                resultado += self.ler_escape()
            else:
                resultado += self.caractere_atual
                self.avancar()

        if self.caractere_atual != '"':
            self.erro("literal de string nao finalizado")
        self.avancar()
        return Token(STRING_LITERAL, resultado, linha_inicial, coluna_inicial)

    def obter_proximo_token(self):
        while self.caractere_atual is not None:
            if self.caractere_atual.isspace():
                self.pular_espaco_em_branco()
                continue

            if self.caractere_atual == '/' and self.espiar() == '/':
                self.pular_comentario_linha()
                continue

            if self.caractere_atual == '/' and self.espiar() == '*':
                self.pular_comentario_bloco()
                continue

            if self.caractere_atual.isalpha() or self.caractere_atual == '_':
                return self.identificador_ou_palavra_reservada()

            if self.caractere_atual.isdigit():
                return self.numero()

            if self.caractere_atual == "'":
                return self.literal_caractere()

            if self.caractere_atual == '"':
                return self.literal_string()

            linha = self.linha
            coluna = self.coluna

            if self.caractere_atual == '=':
                if self.espiar() == '=':
                    self.avancar()
                    self.avancar()
                    return Token(IGUAL, '==', linha, coluna)
                self.avancar()
                return Token(ATRIBUICAO, '=', linha, coluna)

            if self.caractere_atual == '!':
                if self.espiar() == '=':
                    self.avancar()
                    self.avancar()
                    return Token(DIFERENTE, '!=', linha, coluna)
                self.avancar()
                return Token(NAO_LOGICO, '!', linha, coluna)

            if self.caractere_atual == '<':
                if self.espiar() == '=':
                    self.avancar()
                    self.avancar()
                    return Token(MENOR_IGUAL, '<=', linha, coluna)
                self.avancar()
                return Token(MENOR, '<', linha, coluna)

            if self.caractere_atual == '>':
                if self.espiar() == '=':
                    self.avancar()
                    self.avancar()
                    return Token(MAIOR_IGUAL, '>=', linha, coluna)
                self.avancar()
                return Token(MAIOR, '>', linha, coluna)

            if self.caractere_atual == '&':
                if self.espiar() == '&':
                    self.avancar()
                    self.avancar()
                    return Token(E_LOGICO, '&&', linha, coluna)
                self.avancar()
                return Token(BIT_E, '&', linha, coluna)

            if self.caractere_atual == '|':
                if self.espiar() == '|':
                    self.avancar()
                    self.avancar()
                    return Token(OU_LOGICO, '||', linha, coluna)
                self.avancar()
                return Token(BIT_OU, '|', linha, coluna)

            tokens_simples = {
                '+': MAIS,
                '-': MENOS,
                '*': MULTIPLICACAO,
                '/': DIVISAO,
                '%': RESTO,
                '^': BIT_XOR,
                '~': BIT_NAO,
                ';': PONTO_VIRGULA,
                ',': VIRGULA,
                '(': ABRE_PAREN,
                ')': FECHA_PAREN,
                '{': ABRE_CHAVE,
                '}': FECHA_CHAVE,
                '[': ABRE_COLCHETE,
                ']': FECHA_COLCHETE,
            }

            tipo = tokens_simples.get(self.caractere_atual)
            if tipo is not None:
                caractere = self.caractere_atual
                self.avancar()
                return Token(tipo, caractere, linha, coluna)

            self.erro(f"caractere nao reconhecido '{self.caractere_atual}'")

        return Token(FIM_DE_ARQUIVO, None, self.linha, self.coluna)
