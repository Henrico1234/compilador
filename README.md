# Compilador Procedural para SaM

Implementacao manual de:

- analise lexica;
- analise sintatica descendente;
- analise semantica com escopos e tipagem;
- geracao de codigo para `assembly SaM`.


## Recursos suportados

- Tipos: `int`, `float`, `char`, `bool`, `string`, `void`
- Variaveis com escopo por funcao e por bloco
- Vetores locais alocados em heap
- Literais inteiros, `float`, `char`, `string` e booleanos
- Atribuicao escalar e por indice de vetor
- Operadores aritmeticos: `+`, `-`, `*`, `/`, `%`
- Operadores relacionais: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Operadores logicos: `&&`, `||`, `!`
- Operadores bit a bit: `&`, `|`, `^`, `~`
- `if` / `else`
- `while`
- Funcoes com parametros
- Chamadas de funcao
- `return`
- Geracao de `assembly SaM`

## Como executar

Exibir o assembly do exemplo embutido:

```bash
python main.py
```

Compilar um arquivo fonte:

```bash
python main.py caminho_do_programa.txt
```

Salvar a saida SaM em arquivo:

```bash
python main.py caminho_do_programa.txt -o programa.sam
```

## Como testar

```bash
python -m unittest discover -s tests
```

## Convencao de chamadas SaM adotada

- O chamador reserva um slot de retorno com `PUSHIMM 0`.
- Em seguida empilha os argumentos.
- `LINK` cria o frame e salva o `FBR`.
- `JSR nome_funcao` desvia para a funcao.
- O callee escreve o retorno em `STOREOFF -(n_parametros + 1)`.
- O retorno acontece com `JUMPIND`.
- O chamador restaura `FBR` com `POPFBR` e remove os argumentos com `ADDSP -n`.

## Vetores e strings

- Vetores locais sao declarados como `int xs[10];`.
- O compilador gera `MALLOC` para reservar espaco na heap.
- O primeiro slot da heap fica reservado para o tamanho, como descrito no PDF do professor.
- Strings usam `PUSHIMMSTR` e podem ser armazenadas em variaveis, passadas para funcoes e comparadas por endereco.

