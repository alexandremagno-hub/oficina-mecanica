import tkinter as tk
from tkinter import ttk

from telas.base import Pagina

# Página de exibição dos pedidos
class TelaExibir(Pagina):
    titulo = "Pedidos"
    subtitulo = "Todos os pedidos cadastrados"

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

    def __init__(self, app):
        super().__init__(app)
        area_tabela = ttk.Frame(self.cartao, style="Cartao.TFrame")
        area_tabela.pack(fill="both", expand=True)
        self.tabela = ttk.Treeview(
            area_tabela, columns=[c[0] for c in self.colunas], show="headings", height=10
        )
        for coluna, titulo, largura in self.colunas:
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(
                coluna,
                width=largura,
                anchor="center" if coluna in ("id", "placa", "situacao") else "w",
            )
        barra_rolagem = ttk.Scrollbar(area_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra_rolagem.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra_rolagem.pack(side="right", fill="y")
        ttk.Button(self.cartao, text="Voltar ao menu", command=lambda: self.app.mostrar("menu")).pack(
            anchor="w", pady=(20, 0)
        )

    # Recarregar os pedidos sempre que a página é aberta
    def ao_mostrar(self):
        self.tabela.delete(*self.tabela.get_children())
        for linha in self.app.banco.listar_pedidos():
            self.tabela.insert("", tk.END, values=linha)
