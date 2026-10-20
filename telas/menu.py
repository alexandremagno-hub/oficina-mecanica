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
            ("Atualizar pedido", None),
            ("Excluir pedido", None),
        ]
        for texto, pagina in opcoes:
            botao = ttk.Button(
                self.cartao, text=texto, width=28, command=lambda p=pagina: self.app.mostrar(p)
            )
            botao.pack(fill="x", pady=4)
            if pagina is None:
                botao.state(["disabled"])
        ttk.Separator(self.cartao).pack(fill="x", pady=12)
        ttk.Button(self.cartao, text="Sair do menu", command=lambda: self.app.mostrar("login")).pack(
            fill="x"
        )
