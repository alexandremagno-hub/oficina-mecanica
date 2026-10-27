# Oficina Mecânica

Protótipo de sistema de gestão de ordens de serviço (OS) para uma oficina mecânica, feito em Python com interface web em Streamlit e banco de dados SQLite.

## Funcionalidades

- Login dos funcionários, com a senha guardada como hash no banco. O administrador acessa todas
  as páginas; os demais funcionários, só Ordens de serviço, Andamento e Abrir OS
- Cadastro de funcionários (nome, usuário, função e data de admissão), com edição, troca de
  senha e desativação de quem saiu da oficina (inativos não entram no sistema)
- Abertura de ordens de serviço (cliente, veículo, placa e serviço)
- Registro automático das datas de entrada e de entrega
- Resumo com a quantidade de OS em cada situação
- Página de faturamento: faturamento do mês e total, OS entregues e ticket médio, gráfico
  mensal separando mão de obra e peças e lista das OS entregues, com filtro por ano
- Tela única de ordens de serviço, com busca por nome, placa ou CPF, filtro por situação e
  ordenação ao clicar no cabeçalho das colunas
- Edição e exclusão (com confirmação) da OS selecionada na tabela
- Quadro de andamento com uma coluna por situação, onde cada OS avança etapa por etapa
  (Na fila → Em andamento → Concluído → Entregue) com um clique; ao concluir, o sistema pergunta
  a mão de obra e as peças colocadas e calcula o total (que pode ser corrigido depois na OS)

## Requisitos

- Python 3
- Streamlit e pandas (`requirements.txt`)

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

O sistema abre no navegador em http://localhost:8501. Também dá para rodar com
`.venv/bin/python app.py` (ou pelo botão Run da IDE, com o interpretador do `.venv` selecionado).

Na primeira execução são criados o administrador `admin` / `admin` e os funcionários
`alexandre` / `123`, `lucas` / `123` e `gabriel` / `666`, com a função "A definir". Entre como
`admin` e troque essas senhas na página Funcionários.

O banco `DB_Oficina` é criado automaticamente na pasta do projeto, de qualquer lugar que o programa seja executado. Ele não é versionado no git. Bancos criados por versões antigas são convertidos automaticamente para o esquema atual ao abrir o programa.

## Estrutura

```
app.py           ponto de entrada: login e menu lateral
navegacao.py     páginas do sistema após o login
banco.py         acesso ao banco SQLite
formatos.py      CPF, nomes, busca e validação dos dados da OS
moeda.py         conversão e formatação de valores em reais
senhas.py        hash e conferência das senhas dos funcionários
paginas/         uma função por página (login, ordens, andamento, faturamento, funcionarios, abrir_os), o formulário da OS
                 e o de mão de obra e peças (valores)
imagens/         logo da barra lateral
.streamlit/      tema da interface
```
