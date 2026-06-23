from dataclasses import dataclass

from analisador_sintatico import (
    AcessoVetor,
    Atribuicao,
    AtribuicaoVetor,
    Bloco,
    ChamadaFuncao,
    DeclaracaoFuncao,
    DeclaracaoVariavel,
    DeclaracaoVetor,
    Enquanto,
    ExpressaoComando,
    LiteralBooleano,
    LiteralCaractere,
    LiteralString,
    Numero,
    OperacaoBinaria,
    OperacaoUnaria,
    Programa,
    Retorno,
    SeEntao,
    Variavel,
)
from tokens_da_linguagem import (
    BIT_E,
    BIT_NAO,
    BIT_OU,
    BIT_XOR,
    DIFERENTE,
    DIVISAO,
    E_LOGICO,
    IGUAL,
    MAIOR,
    MAIOR_IGUAL,
    MAIS,
    MENOR,
    MENOR_IGUAL,
    MENOS,
    MULTIPLICACAO,
    NAO_LOGICO,
    OU_LOGICO,
    RESTO,
)

TIPOS_NUMERICOS = {'int', 'float', 'char'}
TIPOS_INTEGRAIS = {'int', 'char', 'bool'}
TIPOS_ESCALARES = TIPOS_NUMERICOS | {'bool', 'string'}


@dataclass
class Simbolo:
    nome: str
    tipo: str


@dataclass
class SimboloVariavel(Simbolo):
    offset: int
    eh_vetor: bool = False
    tipo_elemento: str = None
    tamanho: int = None


@dataclass
class SimboloFuncao(Simbolo):
    tipos_parametros: list
    nomes_parametros: list
    offset_retorno: int
    quantidade_locais: int = 0
    possui_retorno_expresso: bool = False


class PilhaDeEscopos:
    def __init__(self):
        self._escopos = []

    def entrar_escopo(self):
        self._escopos.append({})

    def sair_escopo(self):
        self._escopos.pop()

    def declarar(self, simbolo):
        escopo_atual = self._escopos[-1]
        if simbolo.nome in escopo_atual:
            raise Exception(f"identificador '{simbolo.nome}' ja declarado neste escopo")
        escopo_atual[simbolo.nome] = simbolo

    def buscar_no_escopo_atual(self, nome):
        return self._escopos[-1].get(nome)

    def buscar(self, nome):
        for escopo in reversed(self._escopos):
            simbolo = escopo.get(nome)
            if simbolo is not None:
                return simbolo
        return None


class NodeVisitor:
    def visit(self, node):
        nome_metodo = f'visit_{type(node).__name__}'
        visitante = getattr(self, nome_metodo, self.erro_visitante_nao_encontrado)
        return visitante(node)

    def erro_visitante_nao_encontrado(self, node):
        raise Exception(f'Nenhum metodo visit_{type(node).__name__} definido')


class AnalisadorSemantico(NodeVisitor):
    def __init__(self):
        self.funcoes = {}
        self.escopos = PilhaDeEscopos()
        self.funcao_atual = None
        self.proximo_offset_local = 2

    def erro(self, mensagem):
        raise Exception(f"Erro Semantico: {mensagem}")
    
    def analisar(self, arvore):
        self.visit(arvore)
        return arvore

    def visit_Programa(self, node: Programa):
        for funcao in node.funcoes:
            self.registrar_assinatura(funcao)

        simbolo_main = self.funcoes.get('main')
        if simbolo_main is None:
            self.erro("funcao 'main' nao declarada")
        if simbolo_main.tipos_parametros:
            self.erro("funcao 'main' deve ser declarada sem parametros")

        for funcao in node.funcoes:
            self.visit(funcao)

    def registrar_assinatura(self, node: DeclaracaoFuncao):
        if node.nome_funcao in self.funcoes:
            self.erro(f"funcao '{node.nome_funcao}' ja declarada")

        tipos_parametros = [parametro.tipo_parametro for parametro in node.parametros]
        nomes_parametros = [parametro.nome_parametro for parametro in node.parametros]
        if len(set(nomes_parametros)) != len(nomes_parametros):
            self.erro(f"funcao '{node.nome_funcao}' possui parametros duplicados")

        simbolo = SimboloFuncao(
            nome=node.nome_funcao,
            tipo=node.tipo_retorno,
            tipos_parametros=tipos_parametros,
            nomes_parametros=nomes_parametros,
            offset_retorno=-(len(tipos_parametros) + 1),
        )
        node.simbolo = simbolo
        self.funcoes[node.nome_funcao] = simbolo


    def visit_DeclaracaoFuncao(self, node: DeclaracaoFuncao):
        self.funcao_atual = node.simbolo
        self.proximo_offset_local = 2
        self.escopos.entrar_escopo()

        for indice, parametro in enumerate(node.parametros):
            offset = -(len(node.parametros) - indice)
            simbolo_parametro = SimboloVariavel(
                parametro.nome_parametro,
                parametro.tipo_parametro,
                offset,
            )
            parametro.simbolo = simbolo_parametro
            try:
                self.escopos.declarar(simbolo_parametro)
            except Exception as exc:
                self.erro(f"na funcao '{node.nome_funcao}': {exc}")

        self.visit_bloco(node.bloco, criar_escopo=False)
        self.funcao_atual.quantidade_locais = self.proximo_offset_local - 2

        if self.funcao_atual.tipo != 'void' and not self.funcao_atual.possui_retorno_expresso:
            self.erro(f"funcao '{node.nome_funcao}' deve possuir ao menos um retorno")

        self.escopos.sair_escopo()
        self.funcao_atual = None

    def visit_Bloco(self, node: Bloco):
        self.visit_bloco(node)

    def visit_bloco(self, node: Bloco, criar_escopo=True):
        if criar_escopo:
            self.escopos.entrar_escopo()
        try:
            for comando in node.comandos:
                self.visit(comando)
        finally:
            if criar_escopo:
                self.escopos.sair_escopo()

    def visit_DeclaracaoVariavel(self, node: DeclaracaoVariavel):
        if self.escopos.buscar_no_escopo_atual(node.nome_variavel) is not None:
            self.erro(f"variavel '{node.nome_variavel}' ja declarada neste escopo")

        simbolo = SimboloVariavel(node.nome_variavel, node.tipo_variavel, self.proximo_offset_local)
        self.proximo_offset_local += 1
        node.simbolo = simbolo
        self.escopos.declarar(simbolo)

        if node.inicializador is not None:
            tipo_expr = self.visit(node.inicializador)
            self.verificar_atribuicao(node.tipo_variavel, tipo_expr, f"inicializacao de '{node.nome_variavel}'")

    def visit_DeclaracaoVetor(self, node: DeclaracaoVetor):
        if node.tipo_elemento == 'void':
            self.erro(f"vetor '{node.nome_vetor}' nao pode ter elementos do tipo void")
        if node.tamanho <= 0:
            self.erro(f"vetor '{node.nome_vetor}' deve ter tamanho positivo")
        if self.escopos.buscar_no_escopo_atual(node.nome_vetor) is not None:
            self.erro(f"variavel '{node.nome_vetor}' ja declarada neste escopo")

        simbolo = SimboloVariavel(
            nome=node.nome_vetor,
            tipo=f'{node.tipo_elemento}[]',
            offset=self.proximo_offset_local,
            eh_vetor=True,
            tipo_elemento=node.tipo_elemento,
            tamanho=node.tamanho,
        )
        self.proximo_offset_local += 1
        node.simbolo = simbolo
        self.escopos.declarar(simbolo)

    def visit_Atribuicao(self, node: Atribuicao):
        simbolo = self.escopos.buscar(node.nome_variavel)
        if simbolo is None:
            self.erro(f"uso de variavel nao declarada: '{node.nome_variavel}'")
        if not isinstance(simbolo, SimboloVariavel) or simbolo.eh_vetor:
            self.erro(f"identificador '{node.nome_variavel}' nao e uma variavel escalar")

        node.simbolo = simbolo
        tipo_expr = self.visit(node.expressao)
        self.verificar_atribuicao(simbolo.tipo, tipo_expr, f"atribuicao para '{node.nome_variavel}'")
        return simbolo.tipo

    def visit_AtribuicaoVetor(self, node: AtribuicaoVetor):
        simbolo = self.escopos.buscar(node.nome_vetor)
        if simbolo is None:
            self.erro(f"uso de vetor nao declarado: '{node.nome_vetor}'")
        if not isinstance(simbolo, SimboloVariavel) or not simbolo.eh_vetor:
            self.erro(f"identificador '{node.nome_vetor}' nao e um vetor")

        tipo_indice = self.visit(node.indice)
        if tipo_indice not in TIPOS_INTEGRAIS:
            self.erro(f"indice do vetor '{node.nome_vetor}' deve ser int, char ou bool")

        tipo_expr = self.visit(node.expressao)
        self.verificar_atribuicao(simbolo.tipo_elemento, tipo_expr, f"atribuicao no vetor '{node.nome_vetor}'")
        node.simbolo = simbolo
        return simbolo.tipo_elemento
    
    def visit_ExpressaoComando(self, node: ExpressaoComando):
        return self.visit(node.expressao)

    def visit_Variavel(self, node: Variavel):
        simbolo = self.escopos.buscar(node.nome)
        if simbolo is None:
            self.erro(f"variavel nao declarada: '{node.nome}'")
        if not isinstance(simbolo, SimboloVariavel) or simbolo.eh_vetor:
            self.erro(f"identificador '{node.nome}' nao e uma variavel escalar")
        node.simbolo = simbolo
        node.tipo_inferido = simbolo.tipo
        return simbolo.tipo

    def visit_AcessoVetor(self, node: AcessoVetor):
        simbolo = self.escopos.buscar(node.nome_vetor)
        if simbolo is None:
            self.erro(f"vetor nao declarado: '{node.nome_vetor}'")
        if not isinstance(simbolo, SimboloVariavel) or not simbolo.eh_vetor:
            self.erro(f"identificador '{node.nome_vetor}' nao e um vetor")

        tipo_indice = self.visit(node.indice)
        if tipo_indice not in TIPOS_INTEGRAIS:
            self.erro(f"indice do vetor '{node.nome_vetor}' deve ser int, char ou bool")

        node.simbolo = simbolo
        node.tipo_inferido = simbolo.tipo_elemento
        return simbolo.tipo_elemento

    def visit_ChamadaFuncao(self, node: ChamadaFuncao):
        simbolo = self.funcoes.get(node.nome_funcao)
        if simbolo is None:
            self.erro(f"funcao nao declarada: '{node.nome_funcao}'")

        if len(node.argumentos) != len(simbolo.tipos_parametros):
            self.erro(
                f"funcao '{node.nome_funcao}' espera {len(simbolo.tipos_parametros)} argumento(s), "
                f"mas recebeu {len(node.argumentos)}"
            )

        for indice, (argumento, tipo_parametro) in enumerate(zip(node.argumentos, simbolo.tipos_parametros), start=1):
            tipo_argumento = self.visit(argumento)
            self.verificar_atribuicao(tipo_parametro, tipo_argumento, f"argumento {indice} de '{node.nome_funcao}'")

        node.simbolo = simbolo
        node.tipo_inferido = simbolo.tipo
        return simbolo.tipo

    def visit_SeEntao(self, node: SeEntao):
        tipo_condicao = self.visit(node.condicao)
        if tipo_condicao not in TIPOS_INTEGRAIS:
            self.erro("a condicao do if deve resultar em int, char ou bool")
        self.visit(node.bloco_verdadeiro)
        if node.bloco_falso is not None:
            self.visit(node.bloco_falso)

    def visit_Enquanto(self, node: Enquanto):
        tipo_condicao = self.visit(node.condicao)
        if tipo_condicao not in TIPOS_INTEGRAIS:
            self.erro("a condicao do while deve resultar em int, char ou bool")
        self.visit(node.bloco)

    def visit_Retorno(self, node: Retorno):
        if self.funcao_atual is None:
            self.erro("comando return fora de funcao")

        tipo_retorno = self.funcao_atual.tipo
        if tipo_retorno == 'void':
            if node.expressao is not None:
                self.erro(f"funcao '{self.funcao_atual.nome}' e void e nao pode retornar valor")
            self.funcao_atual.possui_retorno_expresso = True
            return 'void'

        if node.expressao is None:
            self.erro(f"funcao '{self.funcao_atual.nome}' deve retornar valor do tipo {tipo_retorno}")

        tipo_expr = self.visit(node.expressao)
        self.verificar_atribuicao(tipo_retorno, tipo_expr, f"retorno da funcao '{self.funcao_atual.nome}'")
        self.funcao_atual.possui_retorno_expresso = True
        return tipo_retorno
    

    def visit_OperacaoBinaria(self, node: OperacaoBinaria):
        tipo_esquerda = self.visit(node.esquerda)
        tipo_direita = self.visit(node.direita)
        operador = node.operador.tipo

        if operador in (MAIS, MENOS, MULTIPLICACAO, DIVISAO):
            self.exigir_numericos(tipo_esquerda, tipo_direita, operador)
            node.tipo_inferido = self.tipo_promovido(tipo_esquerda, tipo_direita)
            return node.tipo_inferido

        if operador == RESTO:
            self.exigir_integrais_numericos(tipo_esquerda, tipo_direita, operador)
            node.tipo_inferido = 'int'
            return node.tipo_inferido

        if operador in (IGUAL, DIFERENTE):
            self.exigir_comparaveis(tipo_esquerda, tipo_direita, operador)
            node.tipo_inferido = 'bool'
            return node.tipo_inferido

        if operador in (MAIOR, MENOR, MAIOR_IGUAL, MENOR_IGUAL):
            self.exigir_numericos(tipo_esquerda, tipo_direita, operador)
            node.tipo_inferido = 'bool'
            return node.tipo_inferido

        if operador in (E_LOGICO, OU_LOGICO):
            self.exigir_logicos(tipo_esquerda, tipo_direita, operador)
            node.tipo_inferido = 'bool'
            return node.tipo_inferido

        if operador in (BIT_E, BIT_OU, BIT_XOR):
            self.exigir_integrais_numericos(tipo_esquerda, tipo_direita, operador)
            node.tipo_inferido = 'int'
            return node.tipo_inferido

        self.erro(f"operador binario nao suportado: {operador}")


    def visit_OperacaoUnaria(self, node: OperacaoUnaria):
        tipo_expr = self.visit(node.expressao)
        operador = node.operador.tipo

        if operador in (MAIS, MENOS):
            if tipo_expr not in TIPOS_NUMERICOS:
                self.erro(f"operador unario '{node.operador.valor}' requer operando numerico")
            node.tipo_inferido = 'float' if tipo_expr == 'float' else 'int'
            return node.tipo_inferido

        if operador == NAO_LOGICO:
            if tipo_expr not in TIPOS_INTEGRAIS:
                self.erro("operador '!' requer operando int, char ou bool")
            node.tipo_inferido = 'bool'
            return node.tipo_inferido

        if operador == BIT_NAO:
            if tipo_expr not in {'int', 'char'}:
                self.erro("operador '~' requer operando int ou char")
            node.tipo_inferido = 'int'
            return node.tipo_inferido

        self.erro(f"operador unario nao suportado: {operador}")


    def visit_Numero(self, node: Numero):
        node.tipo_inferido = 'float' if isinstance(node.valor, float) else 'int'
        return node.tipo_inferido

    def visit_LiteralCaractere(self, node: LiteralCaractere):
        node.tipo_inferido = 'char'
        return 'char'

    def visit_LiteralString(self, node: LiteralString):
        node.tipo_inferido = 'string'
        return 'string'

    def visit_LiteralBooleano(self, node: LiteralBooleano):
        node.tipo_inferido = 'bool'
        return 'bool'

    def verificar_atribuicao(self, tipo_destino, tipo_origem, contexto):
        if self.tipos_compativeis(tipo_destino, tipo_origem):
            return
        self.erro(f"incompatibilidade de tipos em {contexto}: nao e possivel atribuir {tipo_origem} em {tipo_destino}")

    def exigir_numericos(self, tipo_a, tipo_b, operador):
        if tipo_a not in TIPOS_NUMERICOS or tipo_b not in TIPOS_NUMERICOS:
            self.erro(f"operador '{self.lexema_operador(operador)}' requer operandos numericos")

    def exigir_integrais_numericos(self, tipo_a, tipo_b, operador):
        if tipo_a not in {'int', 'char'} or tipo_b not in {'int', 'char'}:
            self.erro(f"operador '{self.lexema_operador(operador)}' requer operandos int ou char")

    def exigir_logicos(self, tipo_a, tipo_b, operador):
        if tipo_a not in TIPOS_INTEGRAIS or tipo_b not in TIPOS_INTEGRAIS:
            self.erro(f"operador '{self.lexema_operador(operador)}' requer operandos int, char ou bool")

    def exigir_comparaveis(self, tipo_a, tipo_b, operador):
        if tipo_a in TIPOS_NUMERICOS and tipo_b in TIPOS_NUMERICOS:
            return
        if tipo_a == tipo_b and tipo_a in {'bool', 'string'}:
            return
        self.erro(f"operador '{self.lexema_operador(operador)}' requer operandos compativeis")

    def tipo_promovido(self, tipo_a, tipo_b):
        if 'float' in (tipo_a, tipo_b):
            return 'float'
        return 'int'

    def tipos_compativeis(self, tipo_destino, tipo_origem):
        if tipo_destino == tipo_origem:
            return True
        if tipo_destino == 'float' and tipo_origem in {'int', 'char'}:
            return True
        if tipo_destino == 'int' and tipo_origem == 'char':
            return True
        if tipo_destino == 'bool' and tipo_origem in {'int', 'char'}:
            return True
        return False
    
    def lexema_operador(self, tipo_operador):
        return {
            MAIS: '+',
            MENOS: '-',
            MULTIPLICACAO: '*',
            DIVISAO: '/',
            RESTO: '%',
            IGUAL: '==',
            DIFERENTE: '!=',
            MAIOR: '>',
            MENOR: '<',
            MAIOR_IGUAL: '>=',
            MENOR_IGUAL: '<=',
            E_LOGICO: '&&',
            OU_LOGICO: '||',
            NAO_LOGICO: '!',
            BIT_E: '&',
            BIT_OU: '|',
            BIT_XOR: '^',
            BIT_NAO: '~',
        }.get(tipo_operador, tipo_operador)
