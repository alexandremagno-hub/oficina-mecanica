# Oficina Mecânica

Protótipo de sistema de gestão de ordens de serviço (OS) para uma oficina mecânica, feito em Python com interface web em Streamlit e banco de dados SQLite.

## Funcionalidades

- Login dos funcionários, com a senha guardada como hash no banco. O administrador acessa todas
  as páginas; os demais funcionários, só Ordens de serviço, Andamento e Abrir OS
- Cadastro de funcionários (nome, usuário, função e data de admissão), com edição, troca de
  senha e desativação de quem saiu da oficina (inativos não entram no sistema)
- Abertura de ordens de serviço (cliente, veículo, placa e serviço)
- Registro automático das datas de entrada e de entrega
- Registro de quem abriu cada OS e de quem concluiu o serviço (o funcionário conectado no
  momento), exibido na lista de OS, no quadro de andamento e no dashboard
- Na lista de OS e no quadro de andamento, cada funcionário vê só as entregas que abriu ou
  concluiu ("Minhas entregas"); o administrador vê todas
- Resumo com a quantidade de OS em cada situação
- Dashboard (só o administrador): faturamento do dia e do mês escolhido (ou o
  geral com "Todos os meses"), OS entregues e ticket médio, destaque do funcionário que mais
  entregou e ranking da equipe, gráfico separando mão de obra e peças (por mês, ou por dia com
  um mês escolhido) e lista das OS entregues, tudo com um único filtro de mês no topo
- Tela única de ordens de serviço, com busca por nome, placa ou CPF, filtro por situação e
  ordenação ao clicar no cabeçalho das colunas
- Edição e exclusão da OS numa janela por cima da tela, com confirmação mostrando o que vai
  mudar antes de gravar (também na edição dos funcionários)
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
paginas/         uma função por página (login, ordens, andamento, faturamento = dashboard, funcionarios, abrir_os), o formulário da OS
                 e o de mão de obra e peças (valores)
imagens/         logo da barra lateral
.streamlit/      tema da interface
```
