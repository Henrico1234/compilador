from dataclasses import dataclass, field

from tokens_da_linguagem import *


class AST:
    pass


@dataclass
class Programa(AST):
    funcoes: list


@dataclass
class Parametro(AST):
    tipo_parametro: str
    nome_parametro: str
    simbolo: object = None


@dataclass
class DeclaracaoFuncao(AST):
    tipo_retorno: str
    nome_funcao: str
    parametros: list
    bloco: AST
    simbolo: object = None


@dataclass
class Bloco(AST):
    comandos: list


@dataclass
class DeclaracaoVariavel(AST):
    tipo_variavel: str
    nome_variavel: str
    inicializador: AST = None
    simbolo: object = None


@dataclass
class DeclaracaoVetor(AST):
    tipo_elemento: str
    nome_vetor: str
    tamanho: int
    simbolo: object = None


@dataclass
class Atribuicao(AST):
    nome_variavel: str
    expressao: AST
    simbolo: object = None


@dataclass
class AtribuicaoVetor(AST):
    nome_vetor: str
    indice: AST
    expressao: AST
    simbolo: object = None


@dataclass
class ExpressaoComando(AST):
    expressao: AST


@dataclass
class SeEntao(AST):
    condicao: AST
    bloco_verdadeiro: AST
    bloco_falso: AST = None


@dataclass
class Enquanto(AST):
    condicao: AST
    bloco: AST


@dataclass
class Retorno(AST):
    expressao: AST = None


@dataclass
class OperacaoBinaria(AST):
    esquerda: AST
    operador: Token
    direita: AST
    tipo_inferido: str = None


@dataclass
class OperacaoUnaria(AST):
    operador: Token
    expressao: AST
    tipo_inferido: str = None


@dataclass
class Numero(AST):
    token: Token
    valor: object = field(init=False)
    tipo_inferido: str = None

    def __post_init__(self):
        self.valor = self.token.valor


@dataclass
class LiteralCaractere(AST):
    token: Token
    valor: str = field(init=False)
    tipo_inferido: str = 'char'

    def __post_init__(self):
        self.valor = self.token.valor


@dataclass
class LiteralString(AST):
    token: Token
    valor: str = field(init=False)
    tipo_inferido: str = 'string'

    def __post_init__(self):
        self.valor = self.token.valor


@dataclass
class LiteralBooleano(AST):
    token: Token
    valor: bool = field(init=False)
    tipo_inferido: str = 'bool'

    def __post_init__(self):
        self.valor = self.token.valor


@dataclass
class Variavel(AST):
    token: Token
    nome: str = field(init=False)
    simbolo: object = None
    tipo_inferido: str = None

    def __post_init__(self):
        self.nome = self.token.valor


@dataclass
class AcessoVetor(AST):
    nome_vetor: str
    indice: AST
    simbolo: object = None
    tipo_inferido: str = None


@dataclass
class ChamadaFuncao(AST):
    nome_funcao: str
    argumentos: list
    simbolo: object = None
    tipo_inferido: str = None


class AnalisadorSintatico:
    def __init__(self, analisador_lexico):
        self.analisador_lexico = analisador_lexico
        self.token_atual = self.analisador_lexico.obter_proximo_token()
        self.proximo_token = self.analisador_lexico.obter_proximo_token()

    def erro(self, mensagem="Erro de sintaxe"):
        token = self.token_atual
        raise Exception(
            f"{mensagem}. Token inesperado: {token.tipo} ('{token.valor}') "
            f"na linha {token.linha}, coluna {token.coluna}"
        )

    def avancar(self):
        self.token_atual = self.proximo_token
        self.proximo_token = self.analisador_lexico.obter_proximo_token()

    def consumir(self, tipo_esperado):
        token = self.token_atual
        if token.tipo != tipo_esperado:
            self.erro(f"Esperado token {tipo_esperado}")
        self.avancar()
        return token

    def consumir_tipo(self):
        if self.token_atual.tipo not in TIPOS_PRIMITIVOS:
            self.erro("Esperado um tipo primitivo")
        return self.consumir(self.token_atual.tipo)

    def consumir_tipo_retorno(self):
        if self.token_atual.tipo not in TIPOS_PRIMITIVOS:
            self.erro("Esperado um tipo de retorno")
        return self.consumir(self.token_atual.tipo)

    def consumir_tipo_variavel(self):
        token = self.consumir_tipo()
        if token.tipo == VOID:
            self.erro("Esperado um tipo valido para declaracao")
        return token

    def consumir_tipo_parametro(self):
        if self.token_atual.tipo == VOID:
            self.erro("Parametros nao podem ser do tipo void")
        return self.consumir_tipo()

    def programa(self):
        funcoes = []
        while self.token_atual.tipo != FIM_DE_ARQUIVO:
            funcoes.append(self.declaracao_funcao())
        return Programa(funcoes)

    def declaracao_funcao(self):
        token_tipo = self.consumir_tipo_retorno()
        nome_funcao = self.consumir(IDENTIFICADOR).valor
        self.consumir(ABRE_PAREN)
        parametros = self.parametros_opcionais()
        self.consumir(FECHA_PAREN)
        bloco = self.bloco()
        return DeclaracaoFuncao(TIPOS_PRIMITIVOS[token_tipo.tipo], nome_funcao, parametros, bloco)

    def parametros_opcionais(self):
        parametros = []
        if self.token_atual.tipo == FECHA_PAREN:
            return parametros

        if self.token_atual.tipo == VOID:
            self.consumir(VOID)
            return parametros

        parametros.append(self.parametro())
        while self.token_atual.tipo == VIRGULA:
            self.consumir(VIRGULA)
            parametros.append(self.parametro())
        return parametros

    def parametro(self):
        token_tipo = self.consumir_tipo_parametro()
        nome = self.consumir(IDENTIFICADOR).valor
        return Parametro(TIPOS_PRIMITIVOS[token_tipo.tipo], nome)

    def bloco(self):
        self.consumir(ABRE_CHAVE)
        comandos = []
        while self.token_atual.tipo != FECHA_CHAVE:
            comandos.append(self.comando())
        self.consumir(FECHA_CHAVE)
        return Bloco(comandos)

    def comando(self):
        if self.token_atual.tipo == ABRE_CHAVE:
            return self.bloco()
        if self.token_atual.tipo in (INT, FLOAT, CHAR, BOOL, STRING):
            return self.declaracao()
        if self.token_atual.tipo == IF:
            return self.comando_se()
        if self.token_atual.tipo == WHILE:
            return self.comando_enquanto()
        if self.token_atual.tipo == RETURN:
            return self.comando_retorno()
        return self.expressao_comando()

    def declaracao(self):
        token_tipo = self.consumir_tipo_variavel()
        nome = self.consumir(IDENTIFICADOR).valor
        tipo = TIPOS_PRIMITIVOS[token_tipo.tipo]

        if self.token_atual.tipo == ABRE_COLCHETE:
            self.consumir(ABRE_COLCHETE)
            tamanho = self.consumir(INTEIRO).valor
            self.consumir(FECHA_COLCHETE)
            self.consumir(PONTO_VIRGULA)
            return DeclaracaoVetor(tipo, nome, tamanho)

        inicializador = self.opcional_atribuicao()
        self.consumir(PONTO_VIRGULA)
        return DeclaracaoVariavel(tipo, nome, inicializador)

    def opcional_atribuicao(self):
        if self.token_atual.tipo != ATRIBUICAO:
            return None
        self.consumir(ATRIBUICAO)
        return self.expressao()

    def expressao_comando(self):
        expr = self.expressao()
        self.consumir(PONTO_VIRGULA)
        return ExpressaoComando(expr)

    def comando_se(self):
        self.consumir(IF)
        self.consumir(ABRE_PAREN)
        condicao = self.expressao()
        self.consumir(FECHA_PAREN)
        bloco_verdadeiro = self.comando()

        bloco_falso = None
        if self.token_atual.tipo == ELSE:
            self.consumir(ELSE)
            bloco_falso = self.comando()

        return SeEntao(condicao, bloco_verdadeiro, bloco_falso)

    def comando_enquanto(self):
        self.consumir(WHILE)
        self.consumir(ABRE_PAREN)
        condicao = self.expressao()
        self.consumir(FECHA_PAREN)
        bloco = self.comando()
        return Enquanto(condicao, bloco)

    def comando_retorno(self):
        self.consumir(RETURN)
        expr = None
        if self.token_atual.tipo != PONTO_VIRGULA:
            expr = self.expressao()
        self.consumir(PONTO_VIRGULA)
        return Retorno(expr)

    def expressao(self):
        no = self.expressao_or_logico()
        if self.token_atual.tipo == ATRIBUICAO:
            self.consumir(ATRIBUICAO)
            expressao_direita = self.expressao()
            if isinstance(no, Variavel):
                return Atribuicao(no.nome, expressao_direita)
            if isinstance(no, AcessoVetor):
                return AtribuicaoVetor(no.nome_vetor, no.indice, expressao_direita)
            self.erro("lado esquerdo invalido em atribuicao")
        return no

    def expressao_or_logico(self):
        no = self.expressao_and_logico()
        while self.token_atual.tipo == OU_LOGICO:
            operador = self.consumir(OU_LOGICO)
            no = OperacaoBinaria(no, operador, self.expressao_and_logico())
        return no

    def expressao_and_logico(self):
        no = self.expressao_or_bit()
        while self.token_atual.tipo == E_LOGICO:
            operador = self.consumir(E_LOGICO)
            no = OperacaoBinaria(no, operador, self.expressao_or_bit())
        return no

    def expressao_or_bit(self):
        no = self.expressao_xor_bit()
        while self.token_atual.tipo == BIT_OU:
            operador = self.consumir(BIT_OU)
            no = OperacaoBinaria(no, operador, self.expressao_xor_bit())
        return no

    def expressao_xor_bit(self):
        no = self.expressao_and_bit()
        while self.token_atual.tipo == BIT_XOR:
            operador = self.consumir(BIT_XOR)
            no = OperacaoBinaria(no, operador, self.expressao_and_bit())
        return no

    def expressao_and_bit(self):
        no = self.expressao_igualdade()
        while self.token_atual.tipo == BIT_E:
            operador = self.consumir(BIT_E)
            no = OperacaoBinaria(no, operador, self.expressao_igualdade())
        return no

    def expressao_igualdade(self):
        no = self.expressao_relacional()
        while self.token_atual.tipo in (IGUAL, DIFERENTE):
            operador = self.consumir(self.token_atual.tipo)
            no = OperacaoBinaria(no, operador, self.expressao_relacional())
        return no

    def expressao_relacional(self):
        no = self.expressao_aditiva()
        while self.token_atual.tipo in (MAIOR, MENOR, MAIOR_IGUAL, MENOR_IGUAL):
            operador = self.consumir(self.token_atual.tipo)
            no = OperacaoBinaria(no, operador, self.expressao_aditiva())
        return no

    def expressao_aditiva(self):
        no = self.expressao_multiplicativa()
        while self.token_atual.tipo in (MAIS, MENOS):
            operador = self.consumir(self.token_atual.tipo)
            no = OperacaoBinaria(no, operador, self.expressao_multiplicativa())
        return no

    def expressao_multiplicativa(self):
        no = self.unaria()
        while self.token_atual.tipo in (MULTIPLICACAO, DIVISAO, RESTO):
            operador = self.consumir(self.token_atual.tipo)
            no = OperacaoBinaria(no, operador, self.unaria())
        return no

    def unaria(self):
        if self.token_atual.tipo in (MAIS, MENOS, NAO_LOGICO, BIT_NAO):
            operador = self.consumir(self.token_atual.tipo)
            return OperacaoUnaria(operador, self.unaria())
        return self.primaria()

    def primaria(self):
        token = self.token_atual

        if token.tipo in (INTEIRO, PONTO_FLUTUANTE):
            self.consumir(token.tipo)
            return Numero(token)

        if token.tipo == CARACTERE_LITERAL:
            self.consumir(CARACTERE_LITERAL)
            return LiteralCaractere(token)

        if token.tipo == STRING_LITERAL:
            self.consumir(STRING_LITERAL)
            return LiteralString(token)

        if token.tipo == BOOLEANO_LITERAL:
            self.consumir(BOOLEANO_LITERAL)
            return LiteralBooleano(token)

        if token.tipo == IDENTIFICADOR:
            return self.identificador_primaria()

        if token.tipo == ABRE_PAREN:
            self.consumir(ABRE_PAREN)
            no = self.expressao()
            self.consumir(FECHA_PAREN)
            return no

        self.erro("Erro de sintaxe na expressao")

    def identificador_primaria(self):
        token_identificador = self.consumir(IDENTIFICADOR)
        nome = token_identificador.valor
        if self.token_atual.tipo == ABRE_PAREN:
            self.consumir(ABRE_PAREN)
            argumentos = self.argumentos_opcionais()
            self.consumir(FECHA_PAREN)
            return ChamadaFuncao(nome, argumentos)
        if self.token_atual.tipo == ABRE_COLCHETE:
            self.consumir(ABRE_COLCHETE)
            indice = self.expressao()
            self.consumir(FECHA_COLCHETE)
            return AcessoVetor(nome, indice)
        return Variavel(token_identificador)

    def argumentos_opcionais(self):
        argumentos = []
        if self.token_atual.tipo == FECHA_PAREN:
            return argumentos
        argumentos.append(self.expressao())
        while self.token_atual.tipo == VIRGULA:
            self.consumir(VIRGULA)
            argumentos.append(self.expressao())
        return argumentos

    def analisar(self):
        no_raiz = self.programa()
        if self.token_atual.tipo != FIM_DE_ARQUIVO:
            self.erro("Codigo encontrado apos o fim esperado do programa")
        return no_raiz
