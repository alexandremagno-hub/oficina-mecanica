from tkinter import ttk

from telas.base import Pagina

# Menu de gestão
class TelaMenu(Pagina):
    titulo = "Menu de gestão"
    subtitulo = "Escolha uma opção"

    def __init__(self, app):
        super().__init__(app)
        opcoes = [
            ("Cadastrar pedido", "cadastro"),
            ("Exibir pedidos", "exibir"),
            ("Atualizar pedido", "atualizar"),
            ("Excluir pedido", "excluir"),
        ]
        for texto, pagina in opcoes:
            ttk.Button(
                self.cartao, text=texto, width=28, command=lambda p=pagina: self.app.mostrar(p)
            ).pack(fill="x", pady=4)
        ttk.Separator(self.cartao).pack(fill="x", pady=12)
        ttk.Button(self.cartao, text="Sair do menu", command=lambda: self.app.mostrar("login")).pack(
            fill="x"
        )
