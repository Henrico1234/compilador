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


class GeradorCodigoSaM:
    def __init__(self):
        self.linhas = []
        self.contador_rotulos = 0
        self.funcao_atual = None

    def gerar(self, programa: Programa):
        self.emitir_bootstrap(programa)
        for funcao in programa.funcoes:
            self.visit(funcao)
        return '\n'.join(self.linhas)

    def emitir_bootstrap(self, programa):
        nomes_funcoes = {funcao.nome_funcao for funcao in programa.funcoes}
        if 'main' not in nomes_funcoes:
            raise Exception("Nao foi possivel gerar codigo: funcao 'main' ausente")

        self.emitir('PUSHIMM 0')
        self.emitir('LINK')
        self.emitir('JSR main')
        self.emitir('POPFBR')
        self.emitir('ADDSP -1')
        self.emitir('STOP')
        self.emitir('')

    def emitir(self, linha):
        self.linhas.append(linha)

    def novo_rotulo(self, prefixo):
        self.contador_rotulos += 1
        return f'{prefixo}_{self.contador_rotulos}'

    def visit(self, node):
        nome_metodo = f'visit_{type(node).__name__}'
        visitante = getattr(self, nome_metodo, None)
        if visitante is None:
            raise Exception(f'Nenhum metodo de geracao para {type(node).__name__}')
        return visitante(node)

    def visit_DeclaracaoFuncao(self, node: DeclaracaoFuncao):
        self.funcao_atual = node.simbolo
        self.emitir(f'{node.nome_funcao}:')
        if node.simbolo.quantidade_locais > 0:
            self.emitir(f'ADDSP {node.simbolo.quantidade_locais}')
        self.visit(node.bloco)
        if node.tipo_retorno == 'void':
            if node.simbolo.quantidade_locais > 0:
                self.emitir(f'ADDSP {-node.simbolo.quantidade_locais}')
            self.emitir('JUMPIND')
        self.emitir('')
        self.funcao_atual = None

    def visit_Bloco(self, node: Bloco):
        for comando in node.comandos:
            self.visit(comando)

    def visit_DeclaracaoVariavel(self, node: DeclaracaoVariavel):
        if node.inicializador is None:
            return
        self.gerar_expressao(node.inicializador)
        self.converter_topo_para(node.inicializador.tipo_inferido, node.tipo_variavel)
        self.emitir(f'STOREOFF {node.simbolo.offset}')

    def visit_DeclaracaoVetor(self, node: DeclaracaoVetor):
        self.emitir(f'PUSHIMM {node.tamanho}')
        self.emitir('MALLOC')
        self.emitir(f'STOREOFF {node.simbolo.offset}')

    def visit_Atribuicao(self, node: Atribuicao):
        self.gerar_expressao(node.expressao)
        self.converter_topo_para(node.expressao.tipo_inferido, node.simbolo.tipo)
        self.emitir(f'STOREOFF {node.simbolo.offset}')

    def visit_AtribuicaoVetor(self, node: AtribuicaoVetor):
        self.emitir(f'PUSHOFF {node.simbolo.offset}')
        self.gerar_expressao(node.indice)
        self.converter_topo_para(node.indice.tipo_inferido, 'int')
        self.emitir('ADD')
        self.emitir('PUSHIMM 1')
        self.emitir('ADD')
        self.gerar_expressao(node.expressao)
        self.converter_topo_para(node.expressao.tipo_inferido, node.simbolo.tipo_elemento)
        self.emitir('STOREIND')

    def visit_ExpressaoComando(self, node: ExpressaoComando):
        self.gerar_expressao(node.expressao)
        self.emitir('ADDSP -1')

    def visit_SeEntao(self, node: SeEntao):
        if node.bloco_falso is None:
            rotulo_fim = self.novo_rotulo('fim_if')
            self.gerar_expressao(node.condicao)
            self.emitir('ISNIL')
            self.emitir(f'JUMPC {rotulo_fim}')
            self.visit(node.bloco_verdadeiro)
            self.emitir(f'{rotulo_fim}:')
            return

        rotulo_verdadeiro = self.novo_rotulo('if_true')
        rotulo_fim = self.novo_rotulo('if_end')
        self.gerar_expressao(node.condicao)
        self.emitir(f'JUMPC {rotulo_verdadeiro}')
        self.visit(node.bloco_falso)
        self.emitir(f'JUMP {rotulo_fim}')
        self.emitir(f'{rotulo_verdadeiro}:')
        self.visit(node.bloco_verdadeiro)
        self.emitir(f'{rotulo_fim}:')

    def visit_Enquanto(self, node: Enquanto):
        rotulo_inicio = self.novo_rotulo('while_inicio')
        rotulo_fim = self.novo_rotulo('while_fim')
        self.emitir(f'{rotulo_inicio}:')
        self.gerar_expressao(node.condicao)
        self.emitir('ISNIL')
        self.emitir(f'JUMPC {rotulo_fim}')
        self.visit(node.bloco)
        self.emitir(f'JUMP {rotulo_inicio}')
        self.emitir(f'{rotulo_fim}:')

    def visit_Retorno(self, node: Retorno):
        if node.expressao is not None:
            self.gerar_expressao(node.expressao)
            self.converter_topo_para(node.expressao.tipo_inferido, self.funcao_atual.tipo)
            self.emitir(f'STOREOFF {self.funcao_atual.offset_retorno}')
        if self.funcao_atual.quantidade_locais > 0:
            self.emitir(f'ADDSP {-self.funcao_atual.quantidade_locais}')
        self.emitir('JUMPIND')

    def visit_Programa(self, node: Programa):
        return self.gerar(node)

    def gerar_expressao(self, node):
        return self.visit(node)

    def visit_Numero(self, node: Numero):
        if node.tipo_inferido == 'float':
            self.emitir(f'PUSHIMMF {node.valor}')
        else:
            self.emitir(f'PUSHIMM {node.valor}')

    def visit_LiteralCaractere(self, node: LiteralCaractere):
        self.emitir(f"PUSHIMMCH {self.formatar_caractere(node.valor)}")

    def visit_LiteralString(self, node: LiteralString):
        self.emitir(f'PUSHIMMSTR {self.formatar_string(node.valor)}')

    def visit_LiteralBooleano(self, node: LiteralBooleano):
        self.emitir(f'PUSHIMM {1 if node.valor else 0}')

    def visit_Variavel(self, node: Variavel):
        self.emitir(f'PUSHOFF {node.simbolo.offset}')

    def visit_AcessoVetor(self, node: AcessoVetor):
        self.emitir(f'PUSHOFF {node.simbolo.offset}')
        self.gerar_expressao(node.indice)
        self.converter_topo_para(node.indice.tipo_inferido, 'int')
        self.emitir('ADD')
        self.emitir('PUSHIMM 1')
        self.emitir('ADD')
        self.emitir('PUSHIND')

    def visit_ChamadaFuncao(self, node: ChamadaFuncao):
        self.emitir('PUSHIMM 0')
        for argumento, tipo_parametro in zip(node.argumentos, node.simbolo.tipos_parametros):
            self.gerar_expressao(argumento)
            self.converter_topo_para(argumento.tipo_inferido, tipo_parametro)
        self.emitir('LINK')
        self.emitir(f'JSR {node.nome_funcao}')
        self.emitir('POPFBR')
        if node.argumentos:
            self.emitir(f'ADDSP {-len(node.argumentos)}')

    def visit_OperacaoUnaria(self, node: OperacaoUnaria):
        self.gerar_expressao(node.expressao)
        if node.operador.tipo == MAIS:
            return
        if node.operador.tipo == MENOS:
            if node.tipo_inferido == 'float':
                self.emitir('PUSHIMMF -1.0')
                self.emitir('TIMESF')
            else:
                self.emitir('PUSHIMM -1')
                self.emitir('TIMES')
            return
        if node.operador.tipo == NAO_LOGICO:
            self.emitir('NOT')
            return
        if node.operador.tipo == BIT_NAO:
            self.emitir('BITNOT')
            return
        raise Exception(f"Operador unario nao suportado na geracao: {node.operador.valor}")

    def visit_OperacaoBinaria(self, node: OperacaoBinaria):
        operador = node.operador.tipo

        if operador in (MAIS, MENOS, MULTIPLICACAO, DIVISAO):
            self.gerar_binaria_aritmetica(node)
            return

        if operador == RESTO:
            self.gerar_expressao(node.esquerda)
            self.gerar_expressao(node.direita)
            self.emitir('MOD')
            return

        if operador in (IGUAL, DIFERENTE, MAIOR, MENOR, MAIOR_IGUAL, MENOR_IGUAL):
            self.gerar_binaria_relacional(node)
            return

        if operador == E_LOGICO:
            self.gerar_expressao(node.esquerda)
            self.gerar_expressao(node.direita)
            self.emitir('AND')
            return

        if operador == OU_LOGICO:
            self.gerar_expressao(node.esquerda)
            self.gerar_expressao(node.direita)
            self.emitir('OR')
            return

        if operador == BIT_E:
            self.gerar_expressao(node.esquerda)
            self.gerar_expressao(node.direita)
            self.emitir('BITAND')
            return

        if operador == BIT_OU:
            self.gerar_expressao(node.esquerda)
            self.gerar_expressao(node.direita)
            self.emitir('BITOR')
            return

        if operador == BIT_XOR:
            self.gerar_expressao(node.esquerda)
            self.gerar_expressao(node.direita)
            self.emitir('BITXOR')
            return

        raise Exception(f"Operador binario nao suportado na geracao: {node.operador.valor}")

    def gerar_binaria_aritmetica(self, node: OperacaoBinaria):
        mapa_int = {
            MAIS: 'ADD',
            MENOS: 'SUB',
            MULTIPLICACAO: 'TIMES',
            DIVISAO: 'DIV',
        }
        mapa_float = {
            MAIS: 'ADDF',
            MENOS: 'SUBF',
            MULTIPLICACAO: 'TIMESF',
            DIVISAO: 'DIVF',
        }

        usa_float = node.tipo_inferido == 'float'
        self.gerar_expressao(node.esquerda)
        if usa_float:
            self.converter_topo_para(node.esquerda.tipo_inferido, 'float')
        self.gerar_expressao(node.direita)
        if usa_float:
            self.converter_topo_para(node.direita.tipo_inferido, 'float')
        self.emitir(mapa_float[node.operador.tipo] if usa_float else mapa_int[node.operador.tipo])

    def gerar_binaria_relacional(self, node: OperacaoBinaria):
        if node.esquerda.tipo_inferido == 'string':
            self.gerar_expressao(node.esquerda)
            self.gerar_expressao(node.direita)
            if node.operador.tipo == IGUAL:
                self.emitir('EQUAL')
            else:
                self.emitir('EQUAL')
                self.emitir('ISNIL')
            return

        if node.esquerda.tipo_inferido == 'bool' and node.direita.tipo_inferido == 'bool':
            self.gerar_expressao(node.esquerda)
            self.gerar_expressao(node.direita)
            if node.operador.tipo == IGUAL:
                self.emitir('EQUAL')
            else:
                self.emitir('EQUAL')
                self.emitir('ISNIL')
            return

        usa_float = node.esquerda.tipo_inferido == 'float' or node.direita.tipo_inferido == 'float'
        if usa_float:
            self.gerar_relacional_float(node)
            return

        self.gerar_expressao(node.esquerda)
        self.gerar_expressao(node.direita)

        if node.operador.tipo == IGUAL:
            self.emitir('EQUAL')
        elif node.operador.tipo == DIFERENTE:
            self.emitir('EQUAL')
            self.emitir('ISNIL')
        elif node.operador.tipo == MAIOR:
            self.emitir('GREATER')
        elif node.operador.tipo == MENOR:
            self.emitir('LESS')
        elif node.operador.tipo == MAIOR_IGUAL:
            self.emitir('LESS')
            self.emitir('ISNIL')
        elif node.operador.tipo == MENOR_IGUAL:
            self.emitir('GREATER')
            self.emitir('ISNIL')

    def gerar_relacional_float(self, node: OperacaoBinaria):
        self.gerar_expressao(node.esquerda)
        self.converter_topo_para(node.esquerda.tipo_inferido, 'float')
        self.gerar_expressao(node.direita)
        self.converter_topo_para(node.direita.tipo_inferido, 'float')
        self.emitir('CMPF')

        if node.operador.tipo == IGUAL:
            self.emitir('PUSHIMM 0')
            self.emitir('EQUAL')
        elif node.operador.tipo == DIFERENTE:
            self.emitir('PUSHIMM 0')
            self.emitir('EQUAL')
            self.emitir('ISNIL')
        elif node.operador.tipo == MAIOR:
            self.emitir('PUSHIMM 0')
            self.emitir('GREATER')
        elif node.operador.tipo == MENOR:
            self.emitir('PUSHIMM 0')
            self.emitir('LESS')
        elif node.operador.tipo == MAIOR_IGUAL:
            self.emitir('PUSHIMM 0')
            self.emitir('LESS')
            self.emitir('ISNIL')
        elif node.operador.tipo == MENOR_IGUAL:
            self.emitir('PUSHIMM 0')
            self.emitir('GREATER')
            self.emitir('ISNIL')

    def converter_topo_para(self, tipo_origem, tipo_destino):
        if tipo_origem == tipo_destino:
            return
        if tipo_destino == 'float' and tipo_origem in {'int', 'char', 'bool'}:
            self.emitir('ITOF')
            return
        if tipo_destino in {'int', 'bool'} and tipo_origem in {'char', 'bool', 'int'}:
            return
        raise Exception(f'Conversao nao suportada de {tipo_origem} para {tipo_destino}')

    def formatar_caractere(self, valor):
        escapes = {
            '\n': r"'\n'",
            '\t': r"'\t'",
            '\r': r"'\r'",
            '\0': r"'\0'",
            "'": r"'\''",
            '\\': r"'\\'",
        }
        return escapes.get(valor, repr(valor))

    def formatar_string(self, valor):
        escapes = {
            '\\': r'\\',
            '"': r'\"',
            '\n': r'\n',
            '\t': r'\t',
            '\r': r'\r',
            '\0': r'\0',
        }
        conteudo = ''.join(escapes.get(caractere, caractere) for caractere in valor)
        return f'"{conteudo}"'
