import argparse
from pathlib import Path

from analisador_lexico import AnalisadorLexico
from analisador_semantico import AnalisadorSemantico
from analisador_sintatico import AnalisadorSintatico
from gerador_codigo_sam import GeradorCodigoSaM

CODIGO_EXEMPLO = """
int soma(int a, int b) {
    return a + b;
}

int main() {
    bool ok = true;
    string texto = "compiladores";
    int valores[3];
    char c = 'a';

    valores[0] = soma(2, 3);
    valores[1] = c;
    valores[2] = valores[0] | valores[1];

    if (ok && texto == "compiladores") {
        while (valores[2] < 120) {
            valores[2] = valores[2] + 1;
        }
        return ~valores[2] ^ 1;
    }

    return 0;
}
"""


def compilar_codigo(codigo_fonte):
    # Encadeia as etapas do compilador: lexico, sintatico, semantico e geracao.
    analisador_lexico = AnalisadorLexico(codigo_fonte)
    analisador_sintatico = AnalisadorSintatico(analisador_lexico)
    arvore_sintatica = analisador_sintatico.analisar()

    analisador_semantico = AnalisadorSemantico()
    analisador_semantico.analisar(arvore_sintatica)

    gerador = GeradorCodigoSaM()
    codigo_sam = gerador.gerar(arvore_sintatica)
    return arvore_sintatica, codigo_sam


def carregar_codigo(caminho_entrada):
    # Se nao vier arquivo, usa o exemplo embutido para facilitar teste rapido.
    if caminho_entrada is None:
        return CODIGO_EXEMPLO
    return Path(caminho_entrada).read_text(encoding='utf-8')


def main():
    # Trata argumentos de linha de comando e mostra o resultado da compilacao.
    parser = argparse.ArgumentParser(description='Compilador da linguagem procedural para assembly SaM.')
    parser.add_argument('arquivo', nargs='?', help='Arquivo-fonte da linguagem procedural.')
    parser.add_argument('-o', '--saida', help='Arquivo de saida para o assembly SaM gerado.')
    parser.add_argument('--mostrar-codigo', action='store_true', help='Exibe o codigo-fonte processado antes da compilacao.')
    args = parser.parse_args()

    try:
        codigo_fonte = carregar_codigo(args.arquivo)

        if args.mostrar_codigo:
            print('Codigo-fonte:\n')
            print(codigo_fonte)
            print()

        _, codigo_sam = compilar_codigo(codigo_fonte)

        if args.saida:
            caminho_saida = Path(args.saida)
            caminho_saida.write_text(codigo_sam, encoding='utf-8')
            print(f'Compilacao concluida com sucesso. Codigo SaM gravado em: {caminho_saida}')
        else:
            print('Compilacao concluida com sucesso.\n')
            print(codigo_sam)

    except Exception as erro:
        print(f'[FALHA NA COMPILACAO] {erro}')


if __name__ == '__main__':
    main()
