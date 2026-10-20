# Oficina Mecânica

Protótipo de sistema de gestão de ordens de serviço (OS) para uma oficina mecânica, feito em Python com interface Tkinter e banco de dados SQLite.

## Funcionalidades

- Login de usuários
- Abertura de ordens de serviço (cliente, veículo, placa, serviço e valor)
- Registro automático das datas de entrada e de entrega
- Tela única de ordens de serviço, com busca por nome, placa ou CPF, filtro por situação e
  ordenação ao clicar no cabeçalho das colunas
- Atualização e exclusão de ordens de serviço

## Requisitos

- Python 3
- Tkinter 

## Como rodar

```bash
python3 main.py
```

Usuários de teste: `alexandre` / `123`, `lucas` / `123` e `gabriel` / `666`.

O banco `DB_Oficina` é criado automaticamente na pasta do projeto, de qualquer lugar que o programa seja executado. Ele não é versionado no git. Bancos criados por versões antigas são convertidos automaticamente para o esquema atual ao abrir o programa.

## Estrutura

```
main.py          ponto de entrada
app.py           janela principal e navegação entre telas
banco.py         acesso ao banco SQLite
estilos.py       cores e estilos da interface
moeda.py         conversão e formatação de valores em reais
telas/           uma classe por tela (login, menu, cadastro, pedidos, editar)
```
