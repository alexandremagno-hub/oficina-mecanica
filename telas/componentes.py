import tkinter as tk
from tkinter import ttk

# Tabela com rolagem que lista os pedidos
class TabelaPedidos(ttk.Frame):
    colunas = [
        ("id", "Nº", 50),
        ("cpf", "CPF", 110),
        ("nome", "Cliente", 140),
        ("veiculo", "Veículo", 110),
        ("placa", "Placa", 80),
        ("servico", "Serviço", 140),
        ("valor", "Valor (R$)", 80),
        ("situacao", "Situação", 90),
    ]

    def __init__(self, pai, altura=10):
        super().__init__(pai, style="Cartao.TFrame")
        self.tabela = ttk.Treeview(
            self, columns=[c[0] for c in self.colunas], show="headings", height=altura,
            selectmode="browse",
        )
        for coluna, titulo, largura in self.colunas:
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(
                coluna,
                width=largura,
                anchor="center" if coluna in ("id", "placa", "situacao") else "w",
            )
        barra_rolagem = ttk.Scrollbar(self, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra_rolagem.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra_rolagem.pack(side="right", fill="y")

    def carregar(self, pedidos):
        self.tabela.delete(*self.tabela.get_children())
        for pedido in pedidos:
            self.tabela.insert("", tk.END, values=pedido)

    # Pedido da linha selecionada (id, cpf, nome, veiculo, placa, servico, valor, situacao)
    def selecionado(self):
        selecao = self.tabela.selection()
        if not selecao:
            return None
        return self.tabela.item(selecao[0], "values")

# Formulário com os dados do pedido
class FormularioPedido(ttk.Frame):
    rotulos = [
        "CPF do cliente",
        "Nome do cliente",
        "Modelo do veículo",
        "Placa do veículo",
        "Serviço solicitado",
        "Valor do serviço (R$)",
    ]

    def __init__(self, pai):
        super().__init__(pai, style="Cartao.TFrame")
        self.campos = []
        for linha, rotulo in enumerate(self.rotulos):
            ttk.Label(self, text=rotulo).grid(row=linha, column=0, sticky="w", padx=(0, 15), pady=5)
            campo = ttk.Entry(self, width=32)
            campo.grid(row=linha, column=1, sticky="ew", pady=5)
            self.campos.append(campo)

    # Valores digitados (cpf, nome, veiculo, placa, servico, valor)
    def valores(self):
        cpf, nome, veiculo, placa, servico, valor = (campo.get().strip() for campo in self.campos)
        return cpf, nome.title(), veiculo, placa, servico, valor

    def preencher(self, valores):
        self.limpar()
        for campo, valor in zip(self.campos, valores):
            campo.insert(0, valor)

    def limpar(self):
        for campo in self.campos:
            campo.delete(0, tk.END)

    def focar(self):
        self.campos[0].focus_set()
