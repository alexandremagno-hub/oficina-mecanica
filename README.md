# Oficina Mecânica

Protótipo de sistema de gestão de pedidos para uma oficina mecânica, feito em Python com interface Tkinter e banco de dados SQLite.

## Funcionalidades

- Login de usuários
- Cadastro de pedidos (cliente, veículo, placa, serviço e valor)
- Listagem dos pedidos cadastrados
- Atualização e exclusão de pedidos 

## Requisitos

- Python 3
- Tkinter 

## Como rodar

```bash
python3 main.py
```

Usuários de teste: `alexandre` / `123`, `lucas` / `123` e `gabriel` / `666`.

O banco `DB_Oficina` é criado automaticamente na pasta onde o comando for executado.

## Estrutura

```
main.py          ponto de entrada
app.py           janela principal e navegação entre telas
banco.py         acesso ao banco SQLite
estilos.py       cores e estilos da interface
telas/           uma classe por tela (login, menu, cadastro, exibir)
```
