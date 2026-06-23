import unittest
from pathlib import Path

from analisador_lexico import AnalisadorLexico
from analisador_semantico import AnalisadorSemantico
from analisador_sintatico import AnalisadorSintatico
from gerador_codigo_sam import GeradorCodigoSaM

ARQUIVO_RESULTADO = Path(__file__).resolve().parent.parent / 'resultado_testes.txt'
TESTE_ATUAL = 'teste_desconhecido'


def registrar_resultado(conteudo):
    with ARQUIVO_RESULTADO.open('a', encoding='utf-8') as arquivo:
        arquivo.write(conteudo)
        if not conteudo.endswith('\n'):
            arquivo.write('\n')
        arquivo.write('\n')


def compilar(codigo):
    try:
        arvore = AnalisadorSintatico(AnalisadorLexico(codigo)).analisar()
        AnalisadorSemantico().analisar(arvore)
        codigo_sam = GeradorCodigoSaM().gerar(arvore)
        registrar_resultado(
            f'=== {TESTE_ATUAL} | SUCESSO ===\n'
            f'{codigo_sam}\n'
        )
        return arvore, codigo_sam
    except Exception as erro:
        registrar_resultado(
            f'=== {TESTE_ATUAL} | ERRO ===\n'
            f'{erro}\n'
        )
        raise


class CompiladorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ARQUIVO_RESULTADO.write_text('', encoding='utf-8')

    def setUp(self):
        global TESTE_ATUAL
        TESTE_ATUAL = self._testMethodName

    def test_char_literal_e_underscore(self):
        codigo = """
        int main() {
            char meu_char = 'z';
            return meu_char;
        }
        """
        _, codigo_sam = compilar(codigo)
        self.assertIn("PUSHIMMCH 'z'", codigo_sam)

    def test_escopo_independente_entre_funcoes(self):
        codigo = """
        int f() {
            int x = 1;
            return x;
        }

        int g() {
            int x = 2;
            return x;
        }

        int main() {
            return f() + g();
        }
        """
        _, codigo_sam = compilar(codigo)
        self.assertIn('JSR f', codigo_sam)
        self.assertIn('JSR g', codigo_sam)

    def test_vazamento_de_escopo_entre_funcoes_e_rejeitado(self):
        codigo = """
        int f() {
            int x = 1;
            return x;
        }

        int g() {
            return x;
        }

        int main() {
            return f() + g();
        }
        """
        with self.assertRaisesRegex(Exception, "variavel nao declarada"):
            compilar(codigo)

    def test_incompatibilidade_de_tipos_em_atribuicao(self):
        codigo = """
        int main() {
            int x;
            float y = 3.5;
            x = y;
            return x;
        }
        """
        with self.assertRaisesRegex(Exception, "incompatibilidade de tipos"):
            compilar(codigo)

    def test_parametros_e_retorno_de_funcao(self):
        codigo = """
        float dobro(float valor) {
            return valor + valor;
        }

        int main() {
            float resposta = dobro(2);
            if (resposta >= 4.0) {
                return 1;
            }
            return 0;
        }
        """
        _, codigo_sam = compilar(codigo)
        self.assertIn('ADDF', codigo_sam)
        self.assertIn('CMPF', codigo_sam)

    def test_while_if_e_mod(self):
        codigo = """
        int main() {
            int x = 0;
            while (x < 10) {
                x = x + 1;
            }
            if (x % 2 == 0) {
                return 1;
            }
            return 0;
        }
        """
        _, codigo_sam = compilar(codigo)
        self.assertIn('while_inicio_', codigo_sam)
        self.assertIn('MOD', codigo_sam)

    def test_comando_expressao_exige_chamada_de_funcao(self):
        codigo = """
        int main() {
            1 + 2;
            return 0;
        }
        """
        with self.assertRaisesRegex(Exception, "somente chamadas de funcao"):
            compilar(codigo)

    def test_bool_string_bitwise_e_vetor(self):
        codigo = """
        int main() {
            bool ok = true;
            string texto = "abc";
            int xs[3];
            xs[0] = 1;
            xs[1] = 2;
            xs[2] = xs[0] | xs[1];
            if (ok && texto == "abc") {
                return ~xs[2] ^ 1;
            }
            return 0;
        }
        """
        _, codigo_sam = compilar(codigo)
        self.assertIn('PUSHIMMSTR "abc"', codigo_sam)
        self.assertIn('MALLOC', codigo_sam)
        self.assertIn('PUSHIND', codigo_sam)
        self.assertIn('STOREIND', codigo_sam)
        self.assertIn('BITOR', codigo_sam)
        self.assertIn('BITNOT', codigo_sam)
        self.assertIn('BITXOR', codigo_sam)

    def test_indice_de_vetor_precisa_ser_integral(self):
        codigo = """
        int main() {
            int xs[2];
            float i = 1.5;
            xs[i] = 1;
            return 0;
        }
        """
        with self.assertRaisesRegex(Exception, "indice do vetor"):
            compilar(codigo)


if __name__ == '__main__':
    unittest.main()
