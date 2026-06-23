# Gramatica da Linguagem

# Produções da Gramática (Formato Formal LL1)

Programa -> Declaracao_funcao Lista_declaracao_funcao
Lista_declaracao_funcao -> Declaracao_funcao Lista_declaracao_funcao
Lista_declaracao_funcao -> ε

Declaracao_funcao -> Tipo identificador "(" Parametros_opcionais ")" Bloco

Parametros_opcionais -> Lista_parametros
Parametros_opcionais -> "void"
Parametros_opcionais -> ε

Lista_parametros -> Parametro Resto_parametros
Resto_parametros -> "," Parametro Resto_parametros
Resto_parametros -> ε

Parametro -> Tipo identificador

Bloco -> "{" Lista_comandos "}"

Lista_comandos -> Comando Lista_comandos
Lista_comandos -> ε

Comando -> Bloco
Comando -> Declaracao_variavel
Comando -> Declaracao_vetor
Comando -> Atribuicao
Comando -> Atribuicao_vetor
Comando -> Comando_if
Comando -> Comando_while
Comando -> Comando_retorno
Comando -> Expressao ";"

Declaracao_variavel -> Tipo identificador Opcional_atribuicao ";"
Opcional_atribuicao -> "=" Expressao
Opcional_atribuicao -> ε

Declaracao_vetor -> Tipo identificador "[" inteiro "]" ";"

Atribuicao -> identificador "=" Expressao ";"

Atribuicao_vetor -> identificador "[" Expressao "]" "=" Expressao ";"

Comando_if -> "if" "(" Expressao ")" Comando Opcional_else
Opcional_else -> "else" Comando
Opcional_else -> ε

Comando_while -> "while" "(" Expressao ")" Comando

Comando_retorno -> "return" Opcional_expressao ";"
Opcional_expressao -> Expressao
Opcional_expressao -> ε

Expressao -> Expressao_or_logico

Expressao_or_logico -> Expressao_and_logico Resto_or_logico
Resto_or_logico -> "||" Expressao_and_logico Resto_or_logico
Resto_or_logico -> ε

Expressao_and_logico -> Expressao_or_bit Resto_and_logico
Resto_and_logico -> "&&" Expressao_or_bit Resto_and_logico
Resto_and_logico -> ε

Expressao_or_bit -> Expressao_xor_bit Resto_or_bit
Resto_or_bit -> "|" Expressao_xor_bit Resto_or_bit
Resto_or_bit -> ε

Expressao_xor_bit -> Expressao_and_bit Resto_xor_bit
Resto_xor_bit -> "^" Expressao_and_bit Resto_xor_bit
Resto_xor_bit -> ε

Expressao_and_bit -> Expressao_igualdade Resto_and_bit
Resto_and_bit -> "&" Expressao_igualdade Resto_and_bit
Resto_and_bit -> ε

Expressao_igualdade -> Expressao_relacional Resto_igualdade
Resto_igualdade -> "==" Expressao_relacional Resto_igualdade
Resto_igualdade -> "!=" Expressao_relacional Resto_igualdade
Resto_igualdade -> ε

Expressao_relacional -> Expressao_aditiva Resto_relacional
Resto_relacional -> ">" Expressao_aditiva Resto_relacional
Resto_relacional -> "<" Expressao_aditiva Resto_relacional
Resto_relacional -> ">=" Expressao_aditiva Resto_relacional
Resto_relacional -> "<=" Expressao_aditiva Resto_relacional
Resto_relacional -> ε

Expressao_aditiva -> Expressao_multiplicativa Resto_aditiva
Resto_aditiva -> "+" Expressao_multiplicativa Resto_aditiva
Resto_aditiva -> "-" Expressao_multiplicativa Resto_aditiva
Resto_aditiva -> ε

Expressao_multiplicativa -> Unaria Resto_multiplicativa
Resto_multiplicativa -> "*" Unaria Resto_multiplicativa
Resto_multiplicativa -> "/" Unaria Resto_multiplicativa
Resto_multiplicativa -> "%" Unaria Resto_multiplicativa
Resto_multiplicativa -> ε

Unaria -> "+" Unaria
Unaria -> "-" Unaria
Unaria -> "!" Unaria
Unaria -> "~" Unaria
Unaria -> Primaria

Primaria -> inteiro
Primaria -> ponto_flutuante
Primaria -> caractere
Primaria -> string
Primaria -> booleano
Primaria -> identificador
Primaria -> Acesso_vetor
Primaria -> Chamada_funcao
Primaria -> "(" Expressao ")"

Acesso_vetor -> identificador "[" Expressao "]"

Chamada_funcao -> identificador "(" Argumentos_opcionais ")"

Argumentos_opcionais -> Lista_argumentos
Argumentos_opcionais -> ε

Lista_argumentos -> Expressao Resto_argumentos
Resto_argumentos -> "," Expressao Resto_argumentos
Resto_argumentos -> ε

Tipo -> "int"
Tipo -> "float"
Tipo -> "char"
Tipo -> "bool"
Tipo -> "string"
Tipo -> "void"

## Regras semanticas implementadas

- Escopo por funcao e por bloco.
- Parametros fazem parte do escopo da funcao.
- Variaveis e vetores devem ser declarados antes do uso.
- `main` deve existir e ser declarada sem parametros.
- Funcoes nao `void` devem possuir ao menos um `return` com valor compativel.
- Atribuicoes e argumentos aceitam:
  - mesmo tipo;
  - `char -> int`;
  - `char -> float`;
  - `int -> float`;
  - `int/char -> bool`.
- Operacoes aritmeticas aceitam `int`, `float` e `char`.
- `%`, `&`, `|`, `^` e `~` bit a bit aceitam `int` e `char`.
- `&&`, `||`, `!`, `if` e `while` aceitam `int`, `char` e `bool`.
- Comparacoes numericas retornam `bool`.
- Vetores sao alocados em heap e acessados por indice integral.
- Strings sao tratadas como enderecos retornados por `PUSHIMMSTR`.

## Tokens reconhecidos

- Identificadores com letras, digitos e `_`, desde que nao comecem por digito.
- Literais inteiros: `0`, `10`, `42`
- Literais `float`: `3.14`, `0.5`
- Literais `char`: `'a'`, `'\n'`, `'\t'`, `'\0'`, `'\''`, `'\\'`
- Literais `string`: `"abc"`, `"linha\\nseguinte"`
- Literais booleanos: `true`, `false`
- Comentarios:
  - linha: `// comentario`
  - bloco: `/* comentario */`


